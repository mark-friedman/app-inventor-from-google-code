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
Tests the scoreboard extension.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from game_server.extensions import scoreboard
from game_server.utils import check_playerid
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

def test_add_to_score():
  iid = test_utils.make_instance_with_players()
  score = 100

  # Add the first player to the scoreboard
  change_response = add_to_score(iid, firstpid, score)
  response = test_utils.post_server_command(iid, 'scb_get_scoreboard', [])
  assert response['contents']==change_response['contents']
  assert [score, firstpid] in response['contents']

  # Increment first players score and add another player
  add_to_score(iid, firstpid, score)
  add_to_score(iid, players[1], score)
  response = test_utils.post_server_command(iid, 'scb_get_scoreboard', [])
  assert [score * 2, players[0]] in response['contents']
  assert [score, check_playerid(players[1])] in response['contents']

def test_scoreboard_rejects_unknown_players():
  iid = test_utils.make_instance_with_players()

  #Try to add a scoreboard entry for a player not in the game, it should fail.
  fake_player = "fakeymcfakerson@test.com"
  args = [fake_player, 42]
  test_utils.post_server_command(iid, 'scb_add_to_score', args,
                                 error_expected = True, pid=fake_player)
  response = test_utils.post_server_command(iid, 'scb_get_scoreboard', [])
  assert [42, fake_player] not in response['contents']

def test_set_score():
  iid = test_utils.make_instance_with_players()
  response = set_score(iid, firstpid, 100)
  assert [100, firstpid] == response['contents'][0]
  set_score(iid, firstpid, 200)
  response = set_score(iid, players[1], 400)
  assert [400, check_playerid(players[1])] == response['contents'][0]
  assert [200, firstpid] == response['contents'][1]

def test_get_score():
  iid = test_utils.make_instance_with_players()
  set_score(iid, firstpid, 100)
  set_score(iid, players[1], 200)
  assert get_score(iid, firstpid)[0] == 100
  assert get_score(iid, players[1])[0] == 200
  assert get_score(iid, players[2])[0] == 0

def test_get_and_set_score_list():
  iid = test_utils.make_instance_with_players()
  set_score(iid, firstpid, [100, 2])
  set_score(iid, players[1], [200, 1])
  assert get_score(iid, firstpid) == [100, 2]
  assert get_score(iid, players[1]) == [200, 1]
  assert get_score(iid, players[2]) == [0]

def test_clear_and_get_scoreboard():
  iid = test_utils.make_instance_with_players()
  response = set_score(iid, firstpid, 100)
  response = test_utils.post_server_command(iid, 'scb_get_scoreboard', [])
  assert [100, firstpid] in response['contents']
  response = test_utils.post_server_command(iid, 'scb_clear_scoreboard', [])
  assert [0, firstpid] in response['contents']
  response = test_utils.post_server_command(iid, 'scb_get_scoreboard', [])
  assert [0, firstpid] in response['contents']

def test_app_inventor_scoreboard_ordering():
  scores = {'a' : 12, 'b' : 35, 'c' : 19, 'd' : 85, 'e' : 5}
  scoreboard_list = scoreboard.format_scoreboard_for_app_inventor(scores)
  expected = [[85, 'd'], [35, 'b'], [19, 'c'], [12, 'a'], [5, 'e']]
  assert scoreboard_list == expected

def add_to_score(iid, player, score):
  args = [player, score]
  return test_utils.post_server_command(iid, 'scb_add_to_score', args,
                                        pid=player)

def set_score(iid, player, score):
  args = [player, score]
  return test_utils.post_server_command(iid, 'scb_set_score', args,
                                        pid=player)

def get_score(iid, player):
  response = test_utils.post_server_command(iid, 'scb_get_score', [player])
  return response['contents']
