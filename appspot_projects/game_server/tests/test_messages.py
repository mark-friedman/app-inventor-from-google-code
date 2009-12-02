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
import util
from game_server.server import application
from webtest import TestApp

gid = util.gid
firstpid = util.firstpid
app = util.app
players = [firstpid, 'test2@test.com', 'test3@test.com']

def setUp():
  util.clear_data_store()

def test_set_public():
  iid = get_test_game()
  instance = util.get_instance_model(iid)
  assert not instance.public
  app.post('/newmessage', {'gid': gid,
                           'iid' : iid,
                           'mtype' : 'sys_set_public',
                           'mrec' : '[]',
                           'mcont' : '[true]'})
  instance = util.get_instance_model(iid)
  assert instance.public
  app.post('/newmessage', {'gid': gid,
                           'iid' : iid,
                           'mtype' : 'sys_set_public',
                           'mrec' : '[]',
                           'mcont' : '["False"]'})
  response = app.post('/messages', {'gid': gid,
                         'iid' : iid,
                         'mtype' : 'sys_get_public_instances',
                         'mrec' : firstpid,
                         'count': '1000'}).json
  assert iid not in response['cont'][0]['mcont']
  app.post('/newmessage', {'gid': gid,
                           'iid' : iid,
                           'mtype' : 'sys_set_public',
                           'mrec' : '[]',
                           'mcont' : '["true"]'})
  response = app.post('/messages', {'gid': gid,
                         'iid' : iid,
                         'mtype' : 'sys_get_public_instances',
                         'mrec' : firstpid,
                         'count': '1000'}).json
  assert iid in response['cont'][0]['mcont']

def test_join_public():
  iid = get_test_game()
  playerid = 'uninvitedjerk@test.com'
  response = app.post('/acceptinvite',
                      {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  assert response['e'] is True
  assert 'not invited' in response['cont']
  app.post('/newmessage', {'gid': gid,
                           'iid' : iid,
                           'mtype' : 'sys_set_public',
                           'mrec' : '[]',
                           'mcont' : '[true]'}).json
  response = app.post('/acceptinvite',
                      {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  assert response['e'] is False
  
  state = util.get_player_state(iid, playerid)
  assert iid not in state['invited']
  assert iid in state['joined']

def test_join_full_game():
  iid = get_test_game()
  playerid = 'onetoomany@test.com'
  instance = util.get_instance_model(iid)
  players = len(instance.players)
  app.post('/newmessage', {'gid': gid,
                           'iid' : iid,
                           'mtype' : 'sys_set_max_players',
                           'mrec' : '[]',
                           'mcont' : '[%d]' % players})
  app.post('/invite', {'gid': gid, 'iid' : iid, 'inv' : playerid})
  instance = util.get_instance_model(iid)
  assert instance.full
  assert playerid in instance.invited
  assert playerid not in instance.players
  response =   app.post('/acceptinvite',
                        {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  assert response['e'] is True
  instance = util.get_instance_model(iid)
  assert instance.full
  assert playerid in instance.invited
  assert playerid not in instance.players
  app.post('/newmessage', {'gid': gid,
                           'iid' : iid,
                           'mtype' : 'sys_set_max_players',
                           'mrec' : '[]',
                           'mcont' : '[%d]' % (players + 1)})
  response =   app.post('/acceptinvite',
                        {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  instance = util.get_instance_model(iid)
  assert instance.full
  assert playerid not in instance.invited
  assert playerid in instance.players
  app.post('/newmessage', {'gid': gid,
                           'iid' : iid,
                           'mtype' : 'sys_set_max_players',
                           'mrec' : '[]',
                           'mcont' : '[%d]' % 0})
  instance = util.get_instance_model(iid)
  assert not instance.full

def test_scoreboard():
  iid = get_test_game()
  score = 100
  contents = '["%s", "%d"]' % (players[0], 100)
  app.post('/newmessage', {'gid': gid, 'iid' : iid,
                           'mtype' : 'sys_change_scoreboard',
                           'mrec' : '[]', 'mcont' : contents})
  response = app.post('/messages', {'gid': gid,
                                    'iid' : iid,
                                    'mtype' : 'sys_get_scoreboard',
                                    'mrec' : firstpid,
                                    'count': '1000'}).json
  assert '%s: %d' % (firstpid, score) in response['cont'][0]['mcont']
  app.post('/newmessage', {'gid': gid, 'iid' : iid,
                           'mtype' : 'sys_change_scoreboard',
                           'mrec' : '[]', 'mcont' : contents})
  contents = '["%s", "%d"]' % (players[1], 100)
  app.post('/newmessage', {'gid': gid, 'iid' : iid,
                           'mtype' : 'sys_change_scoreboard',
                           'mrec' : '[]', 'mcont' : contents})
  fake_player = "fakeymcfakerson@test.com"
  contents = '["%s", "%d"]' % (fake_player, 100)
  response = app.post('/newmessage', {'gid': gid,
                                      'iid' : iid,
                                      'mtype' : 'sys_change_scoreboard',
                                      'mrec' : '[]',
                                      'mcont' : contents}).json
  assert response['e']
  response = app.post('/messages', {'gid': gid,
                                    'iid' : iid,
                                    'mtype' : 'sys_get_scoreboard',
                                    'mrec' : firstpid,
                                    'count': '1000'}).json
  assert '%s: %d' % (players[0], (score*2)) in response['cont'][0]['mcont']
  assert '%s: %d' % (players[1], score) in response['cont'][0]['mcont']
  assert '%s: %d' % (fake_player, score) not in response['cont'][0]['mcont']
  

def get_test_game():
  iid = util.make_instance()
  for player in players:
    util.add_player(iid, player)
  return iid
