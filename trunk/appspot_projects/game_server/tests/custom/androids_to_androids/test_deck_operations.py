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
from game_server import utils
from game_server.server import application
from game_server.tests import test_utils
from webtest import TestApp

gid = test_utils.gid
firstpid = test_utils.firstpid
app = test_utils.app
init_players = [firstpid, '"Bob Jones" <test2@test.com>', '<test3@test.com>', 'test4@test.com']
players = [utils.check_playerid(pid) for pid in init_players]
player_cards = {}

def setUp():
  test_utils.clear_data_store()

def test_round():
  iid = test_utils.make_instance()
  for player in init_players:
    test_utils.add_player(iid, player)

  # Start the game
  current_round = 1
  response = test_utils.post_server_command(iid, 'ata_new_game', [])

  instance = test_utils.get_instance_model(iid)
  noun_cards_left = len(instance.ata_nouns)
  assert instance.ata_round == current_round

  # Get the cards
  for player in players:
    response = app.post('/messages', {'gid': gid, 'iid' : iid,
                                      'mtype' : 'ata_noun_card', 'pid' : player,
                                      'mtime' : '', 'count' : 10}).json
    cards = response['cont']
    assert len(cards) == 7
    player_cards[player] = [msg['mcont'][0] for msg in cards]

  # Submit cards
  for player in players:
    if player == instance.leader:
      response = test_utils.post_server_command(
          iid, 'ata_noun_card', 
          [current_round, ''],
          pid = player)
      assert response['e'] is True
    else:
      card = player_cards[player].pop()
      response = test_utils.post_server_command(
          iid, 'ata_noun_card', 
          [current_round, card],
          pid = player)
      player_cards[player].append(response['cont']['mcont'][0])
    assert len(player_cards[player]) == 7

  instance = test_utils.get_instance_model(iid)
  assert len(instance.ata_nouns) + len(players) - 1 == noun_cards_left

  player_submissions = {}
  for player in players:
    response = app.post('/messages', {'gid': gid, 'iid' : iid,
                                    'mtype' : 'ata_player_submission', 
                                    'pid' : player,
                                    'mtime' : '', 'count' : 10}).json
    assert len(response['cont']) == len(players) - 1
    for submission in response['cont']:
      assert int(submission['mcont'][0]) == current_round
      player_submissions[submission['mcont'][2]] = submission['mcont'][1]

  # Choose a winner
  winner = [player for player in players if player != instance.leader][0]
  response = test_utils.post_server_command(
      iid, 'ata_end_turn', 
      [current_round, winner, player_submissions[winner]],
      pid = instance.leader)

  current_round = current_round + 1
  instance = test_utils.get_instance_model(iid)
  assert instance.ata_round == current_round
  assert instance.get_score(winner) == 1

  # Check for next round
  for player in players:
    response = app.post('/messages', {'gid': gid, 'iid' : iid,
                                      'mtype' : 'ata_new_round', 
                                      'pid' : player,
                                      'mtime' : '', 'count' : 1}).json
    if player == winner:
      assert get_round(response) == current_round - 1
      response = app.post('/messages', {'gid': gid, 'iid' : iid,
                                      'mtype' : 'ata_char_card', 
                                      'pid' : player,
                                      'mtime' : '', 'count' : 1}).json
      assert get_round(response) == current_round
    else:
      assert get_round(response) == current_round

  # Accelerate the game, next point wins
  for player in players:
    instance.set_score(player, 4)
    instance.put()

  card = 'winning_card'
  winner = [player for player in players if player != instance.leader][0]
  response = test_utils.post_server_command(
      iid, 'ata_end_turn', 
      [current_round, winner, card],
      pid = instance.leader)

  assert response['cont']['mcont'][0] == winner

  # Check for game over messages
  for player in players:
    response = app.post('/messages', {'gid': gid, 'iid' : iid,
                                      'mtype' : 'ata_game_over', 
                                      'pid' : player,
                                      'mtime' : '', 'count' : 1}).json
    winning_message = response['cont'][0]['mcont']
    assert get_round(response) == current_round
    assert winning_message[1] == winner
    assert winning_message[2] == card

    # Make sure no cards are left
    response = app.post('/messages', {'gid': gid, 'iid' : iid,
                                      'mtype' : 'ata_noun_card', 
                                      'pid' : player,
                                      'mtime' : '', 'count' : 10}).json
    assert len(response['cont']) == 0

  instance = test_utils.get_instance_model(iid)
  assert 'ata_round' not in instance.dynamic_properties()

def get_round(message_response):
  return int(message_response['cont'][0]['mcont'][0])
