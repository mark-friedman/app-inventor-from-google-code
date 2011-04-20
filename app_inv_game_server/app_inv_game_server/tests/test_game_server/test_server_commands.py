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
Tests for the server_commands module.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from game_server.utils import check_playerid
from game_server.models.message import Message
from tests import test_utils
from webtest import TestApp

gid = test_utils.gid
firstpid = test_utils.firstpid
app = test_utils.app
players = test_utils.players

def setUp():
  test_utils.clear_data_store()

def tearDown():
  test_utils.clear_data_store()

def test_unknown_command():
  iid = test_utils.make_instance_with_players()
  test_utils.post_server_command(iid, 'bogus_command', [],
                                 error_expected = True)

def test_set_public():
  # Make sure new games are not public
  iid = test_utils.make_instance_with_players()
  instance = test_utils.get_instance_model(iid)
  assert not instance.public

  # Set public to True
  test_utils.post_server_command(iid, 'sys_set_public', [True])
  instance = test_utils.get_instance_model(iid)
  assert instance.public

  # Set public to False
  test_utils.post_server_command(iid, 'sys_set_public', [False])
  instance = test_utils.get_instance_model(iid)
  assert not instance.public

def test_set_public_with_strings():
  # Make sure new games are not public
  iid = test_utils.make_instance_with_players()

  # Set public to true with lowercase string
  test_utils.post_server_command(iid, 'sys_set_public', ["true"])
  instance = test_utils.get_instance_model(iid)
  assert instance.public

  # Set public to false with lowercase string
  test_utils.post_server_command(iid, 'sys_set_public', ["false"])
  instance = test_utils.get_instance_model(iid)
  assert not instance.public

def test_get_public_instances():
  iid = test_utils.make_instance_with_players()
  response = test_utils.post_server_command(iid,
                                            'sys_get_public_instances', [])
  assert iid not in [i[0] for i in response['contents']]

  test_utils.post_server_command(iid, 'sys_set_public', [True])
  response = test_utils.post_server_command(iid,
                                            'sys_get_public_instances', [])
  assert iid in [i[0] for i in response['contents']]

  test_utils.post_server_command(iid, 'sys_set_public', [False])
  response = test_utils.post_server_command(iid,
                                            'sys_get_public_instances', [])
  assert iid not in [i[0] for i in response['contents']]

def test_get_public_instances_with_player_counts():
  test_utils.clear_data_store()
  iid = test_utils.make_instance_with_players()
  test_utils.post_server_command(iid, 'sys_set_public', [True])

  instance = test_utils.get_instance_model(iid)
  players = len(instance.players)

  response = test_utils.post_server_command('',
                                            'sys_get_public_instances', [])
  assert [iid, 3, 0] in response['contents']

  test_utils.post_server_command(iid, 'sys_set_max_players', [players + 1])
  response = test_utils.post_server_command(iid,
                                            'sys_get_public_instances', [])
  assert [iid, players, players + 1] in response['contents']

  test_utils.post_server_command(iid, 'sys_set_max_players', [0])
  response = test_utils.post_server_command(iid,
                                            'sys_get_public_instances', [])
  assert [iid, players, 0] in response['contents']

def test_join_public():
  iid = test_utils.make_instance_with_players()

  # Make sure that an uninvited player cannot join.
  playerid = 'uninvitedjerk@test.com'
  response = app.post('/joininstance',
                      {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  assert response['e'] is True
  assert 'not invited' in response['response']

  # Set the game to public and confirm that uninvited players can join.
  test_utils.post_server_command(iid, 'sys_set_public', [True])
  response = app.post('/joininstance',
                      {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  assert response['e'] is False

  state = test_utils.get_invited_and_joined_instances(iid, playerid)
  assert iid not in state['invited']
  assert iid in state['joined']

def test_join_full_game():
  iid = test_utils.make_instance_with_players()
  playerid = 'onetoomany@test.com'
  instance = test_utils.get_instance_model(iid)
  players = len(instance.players)

  # Set the maximum membership to the current number of players
  test_utils.post_server_command(iid, 'sys_set_max_players', [players])

  # Invite someone new, confirm that they cannot join the instance.
  app.post('/invite', {'gid': gid, 'iid' : iid, 'inv' : playerid})
  instance = test_utils.get_instance_model(iid)
  assert instance.full
  assert playerid in instance.invited
  assert playerid not in instance.players
  response =   app.post('/joininstance',
                        {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  assert response['e'] is True
  instance = test_utils.get_instance_model(iid)
  assert instance.full
  assert playerid in instance.invited
  assert playerid not in instance.players

  # Increase the maximum membership by one, retry joining
  test_utils.post_server_command(iid, 'sys_set_max_players', [players + 1])
  response =   app.post('/joininstance',
                        {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  instance = test_utils.get_instance_model(iid)
  assert instance.full
  assert playerid not in instance.invited
  assert playerid in instance.players
  test_utils.post_server_command(iid, 'sys_set_max_players', [0])
  instance = test_utils.get_instance_model(iid)
  assert not instance.full

def test_delete_instance():
  test_iid = test_utils.make_instance()
  state = test_utils.get_invited_and_joined_instances(test_iid, firstpid)
  assert test_iid in state['joined']
  test_utils.post_server_command(test_iid, 'sys_delete_instance', [])
  assert not test_utils.get_instance_model(test_iid)
  state = test_utils.get_invited_and_joined_instances('', firstpid)
  assert test_iid not in state['joined']

def test_delete_instance_and_messages():
  test_iid = test_utils.make_instance()
  instance = test_utils.get_instance_model(test_iid)
  for i in xrange(10):
    message = Message(parent = instance,
                      sender = firstpid,
                      msg_type = 'blah',
                      recipient = firstpid,
                      content = '%d' % i)
    message.put()
  messages = Message.all(keys_only = True).ancestor(instance.key()).fetch(1000)
  assert len(messages) == 10
  test_utils.post_server_command(test_iid, 'sys_delete_instance', [])
  messages = Message.all(keys_only = True).ancestor(instance.key()).fetch(1000)
  assert len(messages) == 0

def test_decline_invite():
  test_iid = test_utils.make_instance()
  invitee = 'invitee@test.com'
  response = app.post('/invite', {'gid': gid, 'iid' : test_iid,
                                  'inv' : invitee}).json
  assert response['e'] is False
  assert response['response']['inv'] == invitee
  assert response['request_type'] == '/invite'

  state = test_utils.get_invited_and_joined_instances(test_iid, invitee)
  assert test_iid in state['invited']

  test_utils.post_server_command(test_iid, 'sys_decline_invite', [],
                                 pid = invitee)
  state = test_utils.get_invited_and_joined_instances(test_iid, invitee)
  assert test_iid not in state['invited']
