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
Tests the Bulls and Cows custom module.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from tests import test_utils
from google.appengine.ext.db import Key
from game_server.models.message import Message

gid = test_utils.gid
firstpid = test_utils.firstpid
app = test_utils.app

def setUp():
  test_utils.clear_data_store()

def test_wrong_size_guess():
  iid = test_utils.make_instance()
  game_id = new_game(iid)
  test_utils.post_server_command(iid, 'bac_guess', [game_id, ['Blue']],
                                 error_expected = True)

def test_with_two_players():
  iid = test_utils.make_instance()
  test_utils.add_player(iid, 'bob@gmail.com')
  game_id = new_game(iid)
  bob_game_id = new_game(iid, 'bob@gmail.com')
  assert get_game(iid, game_id)
  assert get_game(iid, bob_game_id)

def test_out_of_guesses():
  iid = test_utils.make_instance()
  game_id = new_game(iid)
  game = get_game(iid, game_id)
  game.bac_guesses_remaining = 0
  game.put()
  guess = ['Blue', 'Yellow', 'Green', 'Red']
  test_utils.post_server_command(iid, 'bac_guess', [game_id, [guess]],
                                 error_expected = True)

def test_guesses():
  iid = test_utils.make_instance()
  game_id = new_game(iid)
  game = get_game(iid, game_id)
  guess = game.bac_solution[::-1]
  score = game.bac_score
  guesses = game.bac_guesses_remaining
  response = test_utils.post_server_command(iid, 'bac_guess', [game_id, guess])
  assert response['contents'] == [guesses - 1, score - 4, 0, 4]
  guess = [game.bac_solution[0]]*4
  response = test_utils.post_server_command(iid, 'bac_guess', [game_id, guess])
  assert response['contents'] == [guesses - 2, score - 7, 1, 3]

def test_got_solution():
  iid = test_utils.make_instance()
  game_id = new_game(iid)
  game = get_game(iid, game_id)
  guess = game.bac_solution
  score = game.bac_score
  guesses = game.bac_guesses_remaining
  response = test_utils.post_server_command(iid, 'bac_guess', [game_id, guess])
  assert response['contents'] == [[score, score, 1], True]
  game = get_game(iid, game_id)
  assert game.bac_guesses_remaining == 0

def test_guess_before_new_game():
  iid = test_utils.make_instance()
  test_utils.post_server_command(iid, 'bac_guess', ['a', 'b', 'c', 'd'],
                                 error_expected = True)

def test_resend_guess():
  iid = test_utils.make_instance()
  game_id = new_game(iid)
  game = get_game(iid, game_id)
  guess = game.bac_solution[::-1]
  score = game.bac_score
  guesses = game.bac_guesses_remaining
  response = test_utils.post_server_command(iid, 'bac_guess', [game_id, guess])
  assert response['contents'] == [guesses - 1, score - 4, 0, 4]
  response = test_utils.post_server_command(iid, 'bac_guess', [game_id, guess])
  assert response['contents'] == [guesses - 1, score - 4, 0, 4]
  guess = [game.bac_solution[0]]*4
  response = test_utils.post_server_command(iid, 'bac_guess', [game_id, guess])
  assert response['contents'] == [guesses - 2, score - 7, 1, 3]
  response = test_utils.post_server_command(iid, 'bac_guess', [game_id, guess])
  assert response['contents'] == [guesses - 2, score - 7, 1, 3]
  guess = game.bac_solution
  response = test_utils.post_server_command(iid, 'bac_guess', [game_id, guess])
  assert response['contents'] == [[score - 7, score - 7, 1], True]
  response = test_utils.post_server_command(iid, 'bac_guess', [game_id, guess])
  assert response['contents'] == [[score - 7, score - 7, 1], True]

def test_two_games_at_once():
  bob = 'bob@gmail.com'
  iid = test_utils.make_instance()
  test_utils.add_player(iid, bob)
  game_id = new_game(iid)
  bob_game_id = new_game(iid, bob)
  game = get_game(iid, game_id)
  bob_game = get_game(iid, bob_game_id)
  guess = game.bac_solution[::-1]
  score = game.bac_score
  response = test_utils.post_server_command(iid, 'bac_guess',
                                            [game_id, guess])
  guess = bob_game.bac_solution
  response = test_utils.post_server_command(iid, 'bac_guess',
                                            [bob_game_id, guess], pid = bob)
  assert response['contents'] == [[score, score, 1], True]
  guess = game.bac_solution
  response = test_utils.post_server_command(iid, 'bac_guess',
                                            [game_id, guess])
  assert response['contents'] == [[score - 4, score - 4, 1], True]

def test_not_your_game():
  bob = 'bob@gmail.com'
  iid = test_utils.make_instance()
  test_utils.add_player(iid, bob)
  game_id = new_game(iid)
  response = test_utils.post_server_command(
      iid, 'bac_guess', [game_id, ['Blue'] * 4], pid = bob,
      error_expected = True)

def new_game(iid, pid = firstpid):
  return test_utils.post_server_command(iid, 'bac_new_game', [],
                                        pid = pid)['contents'][3]

def get_game(iid, game_id):
  key = Key.from_path('Game', gid, 'GameInstance', iid, 'Message', game_id)
  return Message.get(key)
