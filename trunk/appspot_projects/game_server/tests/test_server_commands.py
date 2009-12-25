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
from game_server.utils import check_playerid
from webtest import TestApp

gid = test_utils.gid
firstpid = test_utils.firstpid
app = test_utils.app
players = [firstpid, '"Bob Jones" <test2@test.com>', '<test3@test.com>']

def setUp():
  test_utils.clear_data_store()

def test_set_public():
  # Make sure new games are not public
  iid = get_test_game()
  instance = test_utils.get_instance_model(iid)
  assert not instance.public

  # Set public to true with lowercase string
  test_utils.post_server_command(iid, 'sys_set_public', ["true"])
  instance = test_utils.get_instance_model(iid)
  assert instance.public

  # Set public to false with capitalized string
  test_utils.post_server_command(iid, 'sys_set_public', ["False"])
  response = test_utils.post_server_command(iid, 'sys_get_public_instances', [])
  assert iid not in response['cont']['mcont']

  # Set public to True using boolean
  test_utils.post_server_command(iid, 'sys_set_public', [True])
  response = test_utils.post_server_command(iid, 'sys_get_public_instances', [])
  assert iid in response['cont']['mcont']

def test_join_public():
  iid = get_test_game()

  # Make sure that an uninvited player cannot join.
  playerid = 'uninvitedjerk@test.com'
  response = app.post('/acceptinvite',
                      {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  assert response['e'] is True
  assert 'not invited' in response['cont']

  # Set the game to public and confirm that uninvited players can join.
  test_utils.post_server_command(iid, 'sys_set_public', [True])
  response = app.post('/acceptinvite',
                      {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  assert response['e'] is False
  
  state = test_utils.get_player_state(iid, playerid)
  assert iid not in state['invited']
  assert iid in state['joined']

def test_get_public_player_counts():
  iid = get_test_game()
  test_utils.post_server_command(iid, 'sys_set_public', [True])

  instance = test_utils.get_instance_model(iid)
  players = len(instance.players)

  response = test_utils.post_server_command(iid, 'sys_get_public_instances', [False])
  assert iid in response['cont']['mcont']

  test_utils.post_server_command(iid, 'sys_set_max_players', [players])
  response = test_utils.post_server_command(iid, 'sys_get_public_instances', [True])
  assert '%s (%d/%d)' % (iid, players, players) in response['cont']['mcont']

  response = test_utils.post_server_command(iid, 'sys_set_max_players', [0])
  response = test_utils.post_server_command(iid, 'sys_get_public_instances', [True, 1])
  assert '%s (%d)' % (iid, players) in response['cont']['mcont']

def test_join_full_game():
  iid = get_test_game()
  playerid = 'onetoomany@test.com'
  instance = test_utils.get_instance_model(iid)
  players = len(instance.players)

  # Set the maximum membership to the current number of players
  test_utils.post_server_command(iid, 'sys_set_max_players', [players])

  # Invite someone new, confirm that they cannot accept the invite.
  app.post('/invite', {'gid': gid, 'iid' : iid, 'inv' : playerid})
  instance = test_utils.get_instance_model(iid)
  assert instance.full
  assert playerid in instance.invited
  assert playerid not in instance.players
  response =   app.post('/acceptinvite',
                        {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  assert response['e'] is True
  instance = test_utils.get_instance_model(iid)
  assert instance.full
  assert playerid in instance.invited
  assert playerid not in instance.players

  # Increase the maximum membership by one, retry joining
  test_utils.post_server_command(iid, 'sys_set_max_players', [players + 1])
  response =   app.post('/acceptinvite',
                        {'gid': gid, 'iid' : iid, 'pid' : playerid}).json
  instance = test_utils.get_instance_model(iid)
  assert instance.full
  assert playerid not in instance.invited
  assert playerid in instance.players
  test_utils.post_server_command(iid, 'sys_set_max_players', [0])
  instance = test_utils.get_instance_model(iid)
  assert not instance.full

def test_scoreboard():
  iid = get_test_game()
  score = 100

  # Add the first player to the scoreboard
  change_response = change_scoreboard(iid, firstpid, score)
  response = test_utils.post_server_command(iid, 'sys_get_scoreboard', [])
  assert response['cont']['mcont']==change_response['cont']['mcont']
  assert '%d %s' % (score, firstpid) in response['cont']['mcont']

  # Increment first players score and add another player
  change_scoreboard(iid, firstpid, score)
  change_scoreboard(iid, players[1], score)
  response = test_utils.post_server_command(iid, 'sys_get_scoreboard', [])
  assert '%d %s' % (score * 2, players[0]) in response['cont']['mcont']
  assert '%d %s' % (score, check_playerid(players[1])) in response['cont']['mcont']

def test_scoreboard_rejects_unknown_players():
  iid = get_test_game()

  #Try to add a scoreboard entry for a player not in the game, it should fail.
  fake_player = "fakeymcfakerson@test.com"
  response = change_scoreboard(iid, fake_player, 42)
  assert response['e']
  response = test_utils.post_server_command(iid, 'sys_get_scoreboard', [])
  assert '%d %s' % (42, fake_player) not in response['cont']['mcont']

def change_scoreboard(iid, player, score):
  args = [player, score]
  return test_utils.post_server_command(iid, 'sys_change_scoreboard', args, pid=player)

def get_test_game():
  iid = test_utils.make_instance()
  for player in players:
    test_utils.add_player(iid, player)
  return iid
