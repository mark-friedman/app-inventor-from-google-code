'''
Copyright 2009 Google Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import google.appengine.api
import unittest
from game_server.server import application
from game_server.tests import test_utils
from webtest import TestApp

gid = test_utils.gid
firstpid = test_utils.firstpid
app = test_utils.app

def setUp():
  test_utils.clear_data_store()

def test_new_instance():
  test_iid = 'iid_prefix'
  response = app.post('/newinstance', {'gid': gid, 'iid' : test_iid, 
                                       'pid' : firstpid}).json
  assert response['e'] is False
  assert response['cont'].startswith(test_iid)
  assert response['c'] == '/newinstance'

def test_invite_player():
  test_iid = test_utils.make_instance()
  invitee = 'invitee@test.com'
  response = app.post('/invite', {'gid': gid, 'iid' : test_iid, 
                                  'inv' : invitee}).json
  assert response['e'] is False
  assert response['cont'] == invitee
  assert response['c'] == '/invite'  

  state = test_utils.get_player_state(test_iid, invitee)
  assert test_iid in state['invited']

def test_email_parse():
  invitee = '<Invitee> invitee@test.com'
  invitee_email = 'invitee@test.com'
  test_iid = test_utils.make_instance()
  response = app.post('/invite', {'gid': gid, 'iid' : test_iid, 
                                  'inv' : invitee}).json
  assert response['cont'] == invitee_email
  state = test_utils.get_player_state(test_iid, invitee_email)
  assert test_iid in state['invited']
  state = test_utils.get_player_state(test_iid, invitee)
  assert test_iid in state['invited']

def test_accept_invite():
  test_iid = test_utils.make_instance()
  invitee = 'test2@test.com'
  app.post('/invite', {'gid': gid, 'iid' : test_iid, 'inv' : invitee})
  response = app.post('/acceptinvite', {'gid': gid, 'iid' : test_iid, 
                                        'pid' : invitee}).json
  assert response['e'] is False
  assert response['c'] == '/acceptinvite'  

  state = test_utils.get_player_state(test_iid, invitee)
  assert state['invited'] == response['cont']['invited']
  assert state['joined'] == response['cont']['joined']
  assert test_iid not in state['invited']
  assert test_iid in state['joined']

def test_set_leader():
  test_iid = test_utils.make_instance()
  new_leader = 'leader@test.com'
  test_utils.add_player(test_iid, new_leader)

  state = test_utils.get_player_state(test_iid, new_leader)
  assert state['leader'] == firstpid

  response = app.post('/setleader', {'gid': gid, 'iid' : test_iid, 
                                     'pid' : firstpid, 
                                     'ldr' : new_leader}).json
  assert response['e'] is False
  assert response['cont'] == new_leader
  assert response['c'] == '/setleader'

  # Make sure that the only the current leader can change who is leader
  response = app.post('/setleader', {'gid': gid, 'iid' : test_iid, 
                                     'pid' : firstpid, 
                                     'ldr' : firstpid}).json
  assert response['e'] is False
  assert response['cont'] == new_leader
  assert response['c'] == '/setleader'

  state = test_utils.get_player_state(test_iid, new_leader)
  assert state['leader'] == new_leader

def test_clear_data():
  test_iid = test_utils.make_instance()
  response = app.post('/getinstance', {'gid': gid, 'iid' : test_iid})
  assert response.json['e'] is False
  test_utils.clear_data_store()
  response = app.post('/getinstance', {'gid': gid, 'iid' : test_iid})
  assert response.json['e'] is True

def test_send_message():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  mcont = '["quack", "duck"]'
  response = app.post('/newmessage', {'gid': gid,
                                      'iid' : test_iid,
                                      'pid' : firstpid,
                                      'mtype' : mtype,
                                      'mrec' : '["' + firstpid + '"]',
                                      'mcont' : mcont}).json
  assert response['e'] is False
  assert response['cont']['mtype'] == mtype
  assert response['c'] == '/newmessage'

  response = app.post('/messages', {'gid': gid,
                                    'iid' : test_iid,
                                    'mtype' : mtype,
                                    'pid' : firstpid,
                                    'time' : '',
                                    'count' : 1}).json
  assert response['e'] is False
  assert response['c'] == '/messages'
  assert len(response['cont']) == 1
  assert response['cont'][0]['mtype'] == mtype
  assert response['cont'][0]['mcont'] == ['quack', 'duck']

def test_only_get_new_messages():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  mcont = '["quack", "duck"]'
  response = app.post('/newmessage', {'gid': gid,
                                      'iid' : test_iid,
                                      'pid' : firstpid,
                                      'mtype' : mtype,
                                      'mrec' : '["' + firstpid + '"]',
                                      'mcont' : mcont}).json

  response = app.post('/messages', {'gid': gid,
                                    'iid' : test_iid,
                                    'mtype' : mtype,
                                    'pid' : firstpid,
                                    'mtime' : '',
                                    'count' : 1}).json

  date = response['cont'][0]['mtime']
  assert date
  response = app.post('/messages', {'gid': gid,
                                    'iid' : test_iid,
                                    'mtype' : mtype,
                                    'pid' : firstpid,
                                    'mtime' : date,
                                    'count' : 1}).json
  assert len(response['cont']) == 0
  response = app.post('/newmessage', {'gid': gid,
                                      'iid' : test_iid,
                                      'pid' : firstpid,
                                      'mtype' : mtype,
                                      'mrec' : '["' + firstpid + '"]',
                                      'mcont' : mcont}).json
  response = app.post('/messages', {'gid': gid,
                                    'iid' : test_iid,
                                    'mtype' : mtype,
                                    'pid' : firstpid,
                                    'mtime' : date,
                                    'count' : 1}).json
  assert len(response['cont']) == 1

def test_messages_email_strip():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  mcont = '["quack", "duck"]'
  app.post('/newmessage', {'gid': gid, 'iid' : test_iid,
                           'pid' : '"Frank Lloyd" <test@test.com>',
                           'mtype' : mtype,
                           'mrec' : '["\\"Bob Jones\\" <test@test.com>"]',
                           'mcont' : mcont}).json

  response = app.post('/messages', {'gid': gid,
                                    'iid' : test_iid,
                                    'mtype' : mtype,
                                    'pid' : '"Bob Johnson" <test@test.com>',
                                    'mtime' : '',
                                    'count' : 1}).json
  assert response['e'] is False
  assert response['cont'][0]['mtype'] == mtype
  assert response['c'] == '/messages'

def test_get_all_types():
  test_iid = test_utils.make_instance()
  mcont = '["quack", "duck"]'
  app.post('/newmessage', {'gid': gid,
                                      'iid' : test_iid,
                                      'pid' : 'test@test.com',
                                      'mtype' : 'type1',
                                      'mrec' : '["' + firstpid + '"]',
                                      'mcont' : mcont}).json
  app.post('/newmessage', {'gid': gid,
                                      'iid' : test_iid,
                                      'pid' : 'test@test.com',
                                      'mtype' : 'type2',
                                      'mrec' : '["' + firstpid + '"]',
                                      'mcont' : mcont}).json
  response = app.post('/messages', {'gid': gid,
                                    'iid' : test_iid,
                                    'pid' : '"Bob Johnson" <test@test.com>',
                                    'mtime' : '',
                                    'count' : 2}).json
  assert response['e'] is False
  assert response['cont'][0]['mtype'] == 'type2'
  assert response['cont'][1]['mtype'] == 'type1'

