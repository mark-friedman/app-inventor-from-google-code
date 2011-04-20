# Copyright 2010 Google Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Tests for the server post commands.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from tests import test_utils
from webtest import TestApp

gid = test_utils.gid
firstpid = test_utils.firstpid
app = test_utils.app

def setUp():
  test_utils.clear_data_store()

def tearDown():
  test_utils.clear_data_store()

def test_get_instance_lists_with_no_game():
  test_utils.clear_data_store()
  assert not test_utils.get_game_model()
  response = app.post('/getinstancelists',
                      {'gid': gid,
                       'iid' : '',
                       'pid' : firstpid}).json
  assert response['gid'] == gid
  assert response['iid'] == ''
  assert response['response']['invited'] == []
  assert response['response']['joined'] == []
  assert test_utils.get_game_model()

def test_join_instance_makes_new_instance():
  test_utils.clear_data_store()
  iid = 'new_iid'
  assert not test_utils.get_game_model()
  assert not test_utils.get_instance_model(iid)
  response = app.post('/joininstance',
                      {'gid': gid,
                       'iid' : iid,
                       'pid' : firstpid}).json
  assert response['iid'] == iid
  assert response['gid'] == gid
  assert response['response']['invited'] == []
  assert response['response']['joined'] == [iid]
  assert test_utils.get_game_model()
  assert test_utils.get_instance_model(iid)

def test_new_instance():
  test_iid = 'iid_prefix'
  response = app.post('/newinstance', {'gid': gid, 'iid' : test_iid,
                                       'pid' : firstpid}).json

  assert response['e'] is False
  iid = response['iid']
  assert iid.startswith(test_iid)
  assert response['request_type'] == '/newinstance'
  assert iid in response['response']['joined']

def test_new_public_instance():
  test_iid = 'iid_prefix'
  response = app.post('/newinstance',
                      {'gid': gid, 'iid' : test_iid,
                       'pid' : firstpid, 'makepublic' : True}).json

  assert response['e'] is False
  iid = response['iid']
  assert iid.startswith(test_iid)
  assert iid in response['response']['joined']
  assert test_utils.get_instance_model(iid).public == True
  response = app.post('/getinstancelists',
                      {'gid': gid,
                       'iid' : '',
                       'pid' : firstpid}).json
  assert response['response']['invited'] == []
  assert iid in response['response']['joined']
  assert iid in response['response']['public']

def test_new_public_instance_false():
  test_iid = 'iid_prefix'
  response = app.post('/newinstance',
                      {'gid': gid, 'iid' : test_iid,
                       'pid' : firstpid, 'makepublic' : False}).json

  assert response['e'] is False
  iid = response['iid']
  assert iid.startswith(test_iid)
  assert iid in response['response']['joined']
  assert test_utils.get_instance_model(iid).public == False

def test_invite_player():
  test_iid = test_utils.make_instance()
  invitee = 'invitee@test.com'
  response = app.post('/invite', {'gid': gid, 'iid' : test_iid,
                                  'inv' : invitee}).json
  assert response['e'] is False
  assert response['response']['inv'] == invitee
  assert response['request_type'] == '/invite'

  state = test_utils.get_invited_and_joined_instances(test_iid, invitee)
  assert test_iid in state['invited']

def test_invite_player_already_joined():
  test_iid = test_utils.make_instance()
  invitee = 'invitee@test.com'
  test_utils.add_player(test_iid, invitee)
  response = app.post('/invite', {'gid': gid, 'iid' : test_iid,
                                  'inv' : invitee}).json
  assert response['e'] is False
  assert response['response']['inv'] == ''
  assert response['request_type'] == '/invite'

  instance_lists = test_utils.get_invited_and_joined_instances(test_iid,
                                                               invitee)
  assert test_iid in instance_lists['joined']
  assert test_iid not in instance_lists['invited']

def test_email_parse():
  invitee = '<Invitee> invitee@test.com'
  invitee_email = 'invitee@test.com'
  test_iid = test_utils.make_instance()
  response = app.post('/invite', {'gid': gid, 'iid' : test_iid,
                                  'inv' : invitee}).json
  assert response['response']['inv'] == invitee_email
  state = test_utils.get_invited_and_joined_instances(test_iid, invitee_email)
  assert test_iid in state['invited']
  state = test_utils.get_invited_and_joined_instances(test_iid, invitee)
  assert test_iid in state['invited']

def test_join_instance():
  test_utils.clear_data_store()
  test_iid = test_utils.make_instance()
  invitee = 'test2@test.com'
  app.post('/invite', {'gid': gid, 'iid' : test_iid, 'inv' : invitee})
  instances = test_utils.get_invited_and_joined_instances(test_iid, invitee)
  assert instances['invited'] == [test_iid]
  assert instances['joined'] == []

  response = app.post('/joininstance', {'gid': gid, 'iid' : test_iid,
                                        'pid' : invitee}).json
  assert response['e'] is False
  assert response['request_type'] == '/joininstance'

  instances = test_utils.get_invited_and_joined_instances(test_iid, invitee)
  assert instances['invited'] == response['response']['invited']
  assert instances['joined'] == response['response']['joined']
  assert test_iid not in instances['invited']
  assert test_iid in instances['joined']

def test_leave_instance():
  test_utils.clear_data_store()
  iid = test_utils.make_instance()
  other = 'new@a.com'
  test_utils.add_player(iid, other)
  response = app.post('/leaveinstance', {'gid': gid, 'iid' : iid,
                                         'pid' : firstpid}).json
  assert response['e'] is False
  assert response['request_type'] == '/leaveinstance'
  assert response['leader'] == ''
  assert response['response']['joined'] == []
  response = app.post('/leaveinstance', {'gid': gid, 'iid' : iid,
                                         'pid' : other}).json
  assert response['e'] is False
  assert response['request_type'] == '/leaveinstance'
  assert response['leader'] == ''
  assert response['iid'] == ''
  assert response['response']['joined'] == []
  response = app.post('/joininstance', {'gid': gid, 'iid' : iid,
                                        'pid' : firstpid}).json
  assert response['e'] is True

def test_set_leader():
  test_iid = test_utils.make_instance()
  new_leader = 'leader@test.com'
  test_utils.add_player(test_iid, new_leader)

  response = app.post('/getinstancelists',
                      {'gid': gid,
                       'iid' : test_iid,
                       'pid' : firstpid}).json
  assert response['leader'] == firstpid

  response = app.post('/setleader', {'gid': gid, 'iid' : test_iid,
                                     'pid' : firstpid,
                                     'leader' : new_leader}).json
  assert response['e'] is False
  assert response['leader'] == new_leader
  assert response['response']['leader_changed'] == True
  assert response['response']['current_leader'] == new_leader
  assert response['request_type'] == '/setleader'

def test_only_leader_can_set_new_leader():
  test_iid = test_utils.make_instance()
  new_player = 'leader@test.com'
  test_utils.add_player(test_iid, new_player)

  response = app.post('/setleader', {'gid': gid, 'iid' : test_iid,
                                     'pid' : new_player,
                                     'leader' : new_player}).json
  assert response['e'] is False
  assert response['leader'] == firstpid
  assert response['response']['leader_changed'] == False
  assert response['response']['current_leader'] == firstpid
  assert response['request_type'] == '/setleader'

  response = app.post('/getinstancelists',
                      {'gid': gid,
                       'iid' : test_iid,
                       'pid' : firstpid}).json
  assert response['leader'] == firstpid

def test_new_leader_must_be_in_game():
  test_iid = test_utils.make_instance()
  fake_player = 'bob@gmail.com'

  response = app.post('/setleader', {'gid': gid, 'iid' : test_iid,
                                     'pid' : firstpid,
                                     'leader' : fake_player}).json
  assert response['e'] is True
  assert response['leader'] == ''
  assert response['request_type'] == '/setleader'

def test_send_and_receive_message():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  contents = ['quack', 'duck']
  test_utils.send_new_message(test_iid, mtype, [firstpid], contents)

  response = test_utils.get_messages(test_iid, mtype, '', 1)
  assert response[0]['type'] == mtype
  assert response[0]['contents'] == ['quack', 'duck']

def test_send_message_to_string():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  contents = ['quack', 'duck']
  test_utils.send_new_message(test_iid, mtype, firstpid, contents)

  response = test_utils.get_messages(test_iid, mtype, '', 1)
  assert response[0]['type'] == mtype
  assert response[0]['contents'] == ['quack', 'duck']

def test_send_message_to_empty():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  contents = ['quack', 'duck']
  test_utils.send_new_message(test_iid, mtype, '', contents)

  response = test_utils.get_messages(test_iid, mtype, '', 1)
  assert response[0]['type'] == mtype
  assert response[0]['contents'] == ['quack', 'duck']

def test_only_get_new_messages():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  contents = ['quack', 'duck']
  test_utils.send_new_message(test_iid, mtype, [firstpid], contents)

  response = test_utils.get_messages(test_iid, mtype, '', 1)
  date = response[0]['mtime']
  assert date
  response = test_utils.get_messages(test_iid, mtype, date, 1)
  assert len(response) == 0
  test_utils.send_new_message(test_iid, mtype, [firstpid], contents)
  response = test_utils.get_messages(test_iid, mtype, date, 1)
  assert len(response) == 1

def test_messages_email_strip():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  contents = ['quack', 'duck']
  recipient = ['"Bob Jones" <test@test.com>']
  test_utils.send_new_message(test_iid, mtype, recipient, contents,
                              pid = '"Frank Lloyd" <test@test.com>')

  response = test_utils.get_messages(test_iid, mtype, '', 1,
                                     pid = '"Bob Johnson" <test@test.com>')
  assert response[0]['type'] == mtype

def test_get_all_types():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  contents = ['quack', 'duck']
  test_utils.send_new_message(test_iid, 'type1', [firstpid], contents)
  test_utils.send_new_message(test_iid, 'type2', [firstpid], contents)
  response = test_utils.get_messages(test_iid, '', '', 2)
  assert response[0]['type'] == 'type1'
  assert response[1]['type'] == 'type2'

def test_send_message_to_multiple_people():
  test_iid = test_utils.make_instance()
  mtype = 'test'
  contents = ['quack', 'duck']
  player2 = 'player2@test.com'
  test_utils.add_player(test_iid, player2)
  test_utils.send_new_message(test_iid, 'type1', [firstpid, player2], contents)
  test_utils.send_new_message(test_iid, 'type2', [firstpid, player2], contents)
  response = test_utils.get_messages(test_iid, '', '', 2)
  assert response[0]['type'] == 'type1'
  assert response[1]['type'] == 'type2'
  response = test_utils.get_messages(test_iid, '', '', 2, pid = player2)
  assert response[0]['type'] == 'type1'
  assert response[1]['type'] == 'type2'

def test_clear_data():
  test_iid = test_utils.make_instance()
  response = app.post('/getinstance', {'gid': gid, 'iid' : test_iid})
  assert response.json['e'] is False
  test_utils.clear_data_store()
  response = app.post('/getinstance', {'gid': gid, 'iid' : test_iid})
  assert response.json['e'] is True
