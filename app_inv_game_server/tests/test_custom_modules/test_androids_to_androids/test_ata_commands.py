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
Tests the Androids to Androids custom module.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from game_server import utils
from game_server.extensions import scoreboard
from game_server.extensions import card_game
from custom_modules.androids_to_androids import decks
from tests import test_utils

gid = test_utils.gid
firstpid = test_utils.firstpid
app = test_utils.app
init_players = [firstpid, '"Bob Jones" <test2@test.com>', '<test3@test.com>',
                'test4@test.com']
players = [utils.check_playerid(pid) for pid in init_players]
player_cards = {}

def setUp():
  test_utils.clear_data_store()

def test_wrong_round():
  iid = test_utils.make_instance()
  for player in init_players:
    test_utils.add_player(iid, player)
  current_round = 1
  response = test_utils.post_server_command(iid, 'ata_new_game', [])
  char_card = response['contents'][0]
  contents = test_utils.post_server_command(iid, 'ata_submit_card', [2, ''],
                                            pid = firstpid)['contents']
  assert isinstance(contents[0], basestring)
  assert len(contents[1]) == 7
  assert contents[2] == current_round
  assert contents[3] == char_card
  contents = test_utils.post_server_command(iid, 'ata_end_turn', [2, ''],
                                            pid = firstpid)['contents']
  assert isinstance(contents[0], basestring)
  assert len(contents[1]) == 7
  assert contents[2] == current_round
  assert contents[3] == char_card

def test_leader_fails_at_submitting():
  iid = test_utils.make_instance()
  for player in init_players:
    test_utils.add_player(iid, player)
  current_round = 1
  response = test_utils.post_server_command(iid, 'ata_new_game', [])
  test_utils.post_server_command(iid, 'ata_submit_card',
                                 [current_round, ''],
                                 pid = firstpid, error_expected = True)

def test_full_game():
  iid = test_utils.make_instance()
  for player in init_players:
    test_utils.add_player(iid, player)

  # Start the game
  current_round = 1
  response = test_utils.post_server_command(iid, 'ata_new_game', [])

  instance = test_utils.get_instance_model(iid)
  noun_cards_left = card_game.cards_left(instance)
  assert instance.ata_round == current_round

  # Get the cards
  for player in players:
    hand = test_utils.get_messages(iid, 'crd_hand', '', 1, pid = player)[0]
    assert len(hand['contents']) == 7
    player_cards[player] = hand['contents']

  player_submissions = {}
  # Submit cards
  for player in players:
    if player != instance.leader:
      card = player_cards[player].pop()
      response = test_utils.post_server_command(iid, 'ata_submit_card',
                                                [current_round, card],
                                                pid = player)
      player_cards[player] = response['contents'][2]
      player_submissions[player] = card
      for c in player_submissions.values():
        assert c in response['contents'][1]
    assert len(player_cards[player]) == 7

  instance = test_utils.get_instance_model(iid)
  assert noun_cards_left - len(players) + 1 == card_game.cards_left(instance)

  for player in players:
    response = test_utils.get_messages(iid, 'ata_submissions', '', 1,
                                       pid = player)[0]
    for c in player_submissions.values():
      assert c in response['contents'][1]
    assert response['contents'][0] == current_round

  # Choose a winner
  winner = [x for x in players if x != instance.leader][0]
  contents = test_utils.post_server_command(iid, 'ata_end_turn',
                                            [current_round,
                                             player_submissions[winner]],
                                            pid = instance.leader)['contents']
  assert contents[2] == 2
  assert contents[3] == winner
  assert contents[4] == player_submissions[winner]
  assert [1, winner] in contents[1]
  current_round = current_round + 1
  instance = test_utils.get_instance_model(iid)
  assert instance.ata_round == current_round

  # Check for next round messages
  for player in players:
    new_round_msg = test_utils.get_messages(iid, 'ata_new_round', '',
                                            1, pid = player)[0]['contents']
    assert new_round_msg[2] == 2
    assert new_round_msg[3] == winner
    assert new_round_msg[4] == player_submissions[winner]

  # Accelerate the game, next point wins
  for player in players:
    scoreboard.set_score(instance, player, 4)
  instance.put()

  winner = [x for x in players if x != instance.leader][0]
  winning_card = player_cards[winner][0]
  test_utils.post_server_command(iid, 'ata_submit_card',
                                 [current_round, winning_card],
                                 pid = winner)
  contents = test_utils.post_server_command(iid, 'ata_end_turn',
                                            [current_round, winning_card],
                                            pid = instance.leader)['contents']
  assert contents[0] == current_round
  assert contents[1] == winning_card
  assert [5, winner] in contents[2]

  # Check for game over messages
  for player in players:
    contents = test_utils.get_messages(iid, 'ata_game_over', '',
                                       1, pid = player)[0]['contents']
    assert contents[0] == current_round
    assert contents[1] == winning_card
    assert [5, winner] in contents[2]

  instance = test_utils.get_instance_model(iid)
  assert 'ata_round' not in instance.dynamic_properties()
  assert 'ata_char_card' not in instance.dynamic_properties()
  assert 'ata_submissions' not in instance.dynamic_properties()

def test_player_left():
  iid = test_utils.make_instance()
  for player in init_players:
    test_utils.add_player(iid, player)

  # Start the game
  current_round = 1
  response = test_utils.post_server_command(iid, 'ata_new_game', [])

  instance = test_utils.get_instance_model(iid)
  noun_cards_left = card_game.cards_left(instance)
  assert instance.ata_round == current_round

  # Get the cards
  for player in players:
    hand = test_utils.get_messages(iid, 'crd_hand', '', 1, pid = player)[0]
    assert len(hand['contents']) == 7
    player_cards[player] = hand['contents']

  player_submissions = {}

  instance = test_utils.get_instance_model(iid)
  removed_player = instance.players[2]
  instance.players.remove(removed_player)
  instance.put()

  card = player_cards[player].pop()
  response = test_utils.post_server_command(iid, 'ata_submit_card',
                                            [current_round, card],
                                            pid = instance.players[1])
  assert len(response['contents']) == 1
  instance = test_utils.get_instance_model(iid)
  assert removed_player in instance.invited
  test_utils.add_player(iid, removed_player)
  # Submit cards
  for player in players:
    if player != instance.leader:
      card = player_cards[player].pop()
      response = test_utils.post_server_command(iid, 'ata_submit_card',
                                                [current_round, card],
                                                pid = player)
      player_cards[player] = response['contents'][2]
      player_submissions[player] = card
      for c in player_submissions.values():
        assert c in response['contents'][1]
    assert len(player_cards[player]) == 7
