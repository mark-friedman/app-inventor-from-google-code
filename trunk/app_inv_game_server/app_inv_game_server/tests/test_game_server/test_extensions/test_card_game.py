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
Tests for the card_game extension.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from game_server.extensions import card_game
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

def test_deal_new_hand():
  iid = test_utils.make_instance_with_players()
  args = [7, True, True, False, players]
  response = test_utils.post_server_command(iid, 'crd_deal_cards', args)
  assert len(response['contents']) == 7
  for player, hand in get_hands(iid).items():
    assert len(hand) == 7
    assert hand == get_player_hand(iid, player)
  assert get_cards_left(iid) == 31
  args = [7, False, True, False, players]
  response = test_utils.post_server_command(iid, 'crd_deal_cards', args)
  assert len(response['contents']) == 7
  for hand in get_hands(iid).values():
    assert len(hand) == 7
  assert get_cards_left(iid) == 10

def test_deal_all_cards():
  iid = test_utils.make_instance_with_players()
  players_list = test_utils.add_player(iid, 'player4@p.com')
  args = [13, True, True, False, players_list]
  response = test_utils.post_server_command(iid, 'crd_deal_cards', args)
  assert len(response['contents']) == 13
  for hand in get_hands(iid).values():
    assert len(hand) == 13
  assert get_cards_left(iid) == 0

def test_deal_too_many_cards():
  iid = test_utils.make_instance_with_players()
  args = [500, True, True, False, players]
  response = test_utils.post_server_command(iid, 'crd_deal_cards', args,
                                            error_expected = True)
  args = [500, True, True, True, players]
  response = test_utils.post_server_command(iid, 'crd_deal_cards', args,
                                            error_expected = False)
  assert len(response['contents']) == 18
  for player, hand in get_hands(iid).items():
    assert len(hand) == (18 if player == firstpid else 17)
  assert get_cards_left(iid) == 0

def test_deal_twice():
  iid = test_utils.make_instance_with_players()
  args = [7, True, True, False, players]
  response = test_utils.post_server_command(iid, 'crd_deal_cards', args)
  args = [7, False, False, False, players]
  response = test_utils.post_server_command(iid, 'crd_deal_cards', args)
  assert len(response['contents']) == 14
  for hand in get_hands(iid).values():
    assert len(hand) == 14
  assert get_cards_left(iid) == 10

def test_pass_cards():
  iid = test_utils.make_instance_with_players()
  args = [7, True, True, False, players]
  response = test_utils.post_server_command(iid, 'crd_deal_cards', args)
  hands = get_hands(iid)

  # Player 2 passes four cards to player 1
  passing_player = check_playerid(players[1])
  initial_hand = hands[passing_player]
  args = [firstpid, initial_hand[3:]]
  response = test_utils.post_server_command(iid, 'crd_pass_cards', args,
                                            pid = passing_player)
  assert response['contents'] == initial_hand[:3]
  hands = get_hands(iid)
  assert len(hands[firstpid]) == 11
  assert hands[firstpid][7:] == initial_hand[3:]

  # Player 1 passes all cards to player 3
  receiving_player = check_playerid(players[2])
  args = [receiving_player, hands[firstpid]]
  response = test_utils.post_server_command(iid, 'crd_pass_cards', args)
  assert response['contents'] == []
  hands = get_hands(iid)
  assert len(hands[firstpid]) == 0
  assert len(hands[receiving_player]) == 18

def test_pass_cards_not_present():
  iid = test_utils.make_instance_with_players()
  args = [7, True, True, False, players]
  response = test_utils.post_server_command(iid, 'crd_deal_cards', args)
  hands = get_hands(iid)

  # Player 2 passes four cards to player 1 that she has and two cards that
  # she doesn't have.
  passing_player = check_playerid(players[1])
  initial_hand = hands[passing_player]
  args = [firstpid,
          ['fake_card_1'] + initial_hand[3:] + ['fake_card_2']]
  response = test_utils.post_server_command(iid, 'crd_pass_cards', args,
                                            pid = passing_player)
  assert response['contents'] == initial_hand[:3]
  hands = get_hands(iid)
  assert len(hands[firstpid]) == 11
  assert hands[firstpid][7:] == initial_hand[3:]

def test_discard():
  iid = test_utils.make_instance_with_players()
  args = [7, True, True, False, players]
  test_utils.post_server_command(iid, 'crd_deal_cards', args)
  initial_hand = get_hands(iid)[firstpid]
  response = test_utils.post_server_command(iid, 'crd_discard',
                                            initial_hand[:3])
  assert response['contents'] == initial_hand[3:]

def test_discard_cards_not_present():
  iid = test_utils.make_instance_with_players()
  args = [7, True, True, False, players]
  test_utils.post_server_command(iid, 'crd_deal_cards', args)
  initial_hand = get_hands(iid)[firstpid]
  to_discard = [initial_hand[0]] + ['%s' % x for x in xrange(12)]
  response = test_utils.post_server_command(iid, 'crd_discard', to_discard)
  assert response['contents'] == initial_hand[1:]

def test_get_cards_remaining():
  iid = test_utils.make_instance_with_players()
  response = test_utils.post_server_command(iid, 'crd_cards_left', [])
  assert response['contents'] == [-1]
  test_utils.post_server_command(iid, 'crd_draw_cards', [5, False])
  response = test_utils.post_server_command(iid, 'crd_cards_left', [])
  assert response['contents'] == [47]

def test_draw_cards():
  iid = test_utils.make_instance_with_players()
  test_utils.post_server_command(iid, 'crd_draw_cards', [5, False])
  hands = get_hands(iid)
  for player, hand in hands.items():
    assert len(hand) == (5 if player == firstpid else 0)
  assert hands[firstpid] == get_player_hand(iid, firstpid)
  assert get_cards_left(iid) == 47

def test_draw_cards_beyond_deck():
  iid = test_utils.make_instance_with_players()
  # Draw too many cards with ignore empty deck set to false.
  # There should be no effect.
  test_utils.post_server_command(iid, 'crd_draw_cards', [75, False],
                                 error_expected = True)
  hands = get_hands(iid)
  for hand in hands.values():
    assert len(hand) == 0
  assert get_cards_left(iid) == -1

  # Draw too many cards with ignore empty deck, should deal all cards.
  test_utils.post_server_command(iid, 'crd_draw_cards', [75, True])
  hands = get_hands(iid)
  for player, hand in hands.items():
    assert len(hand) == (52 if player == firstpid else 0)
  assert get_cards_left(iid) == 0

def test_set_deck():
  iid = test_utils.make_instance_with_players()
  deck = [[n, s] for n in range(14)[4:] for s in  ['Hearts','Spades']]
  missing_cards = [[n, s] for n in range(4)[1:] for s in ['Hearts', 'Spades']]
  response = test_utils.post_server_command(iid, 'crd_set_deck', deck)
  assert response['contents'] == [20]

  # Set deck again, should fail.
  test_utils.post_server_command(iid, 'crd_set_deck', deck,
                                 error_expected = True)
  # Draw all the cards
  response = test_utils.post_server_command(iid, 'crd_draw_cards', [40, True])
  for card in missing_cards:
    assert card not in response['contents']

def get_hands(iid):
  return card_game.get_hand_dictionary(test_utils.get_instance_model(iid))

def get_deck(iid):
  return card_game.get_deck(test_utils.get_instance_model(iid))

def get_cards_left(iid):
  return card_game.cards_left(test_utils.get_instance_model(iid))

def get_player_hand(iid, pid):
  response = test_utils.get_messages(iid, 'crd_hand', '', 1, pid)
  return response[0]['contents']
