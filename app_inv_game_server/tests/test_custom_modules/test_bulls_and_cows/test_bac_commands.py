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

from tests import test_utils

gid = test_utils.gid
firstpid = test_utils.firstpid
app = test_utils.app

def setUp():
  test_utils.clear_data_store()

def test_wrong_size_guess():
  iid = test_utils.make_instance()
  test_utils.post_server_command(iid, 'bac_new_game', [])
  test_utils.post_server_command(iid, 'bac_guess', ['Blue'],
                                 error_expected = True)

def test_too_many_players():
  iid = test_utils.make_instance()
  test_utils.add_player(iid, 'bob@gmail.com')
  test_utils.post_server_command(iid, 'bac_new_game', [],
                                 error_expected = True)

def test_out_of_guesses():
  iid = test_utils.make_instance()
  test_utils.post_server_command(iid, 'bac_new_game', [])
  instance = test_utils.get_instance_model(iid)
  instance.bac_guesses_remaining = 0
  instance.put()
  guess = ['Blue', 'Yellow', 'Green', 'Red']
  test_utils.post_server_command(iid, 'bac_guess', [1,2,3,4],
                                 error_expected = True)

def test_guesses():
  iid = test_utils.make_instance()
  test_utils.post_server_command(iid, 'bac_new_game', [])
  instance = test_utils.get_instance_model(iid)
  guess = instance.bac_solution[::-1]
  score = instance.bac_score
  guesses = instance.bac_guesses_remaining
  response = test_utils.post_server_command(iid, 'bac_guess', guess)
  assert response['contents'] == [guesses - 1, score - 4, 0, 4]
  guess = [instance.bac_solution[0]]*4
  response = test_utils.post_server_command(iid, 'bac_guess', guess)
  assert response['contents'] == [guesses - 2, score - 7, 1, 3]

def test_got_solution():
  iid = test_utils.make_instance()
  test_utils.post_server_command(iid, 'bac_new_game', [])
  instance = test_utils.get_instance_model(iid)
  guess = instance.bac_solution
  score = instance.bac_score
  guesses = instance.bac_guesses_remaining
  response = test_utils.post_server_command(iid, 'bac_guess', guess)
  assert response['contents'] == [guesses - 1, score, score, 1, True]
  instance = test_utils.get_instance_model(iid)
  assert instance.bac_guesses_remaining == 0

def test_guess_before_new_game():
  iid = test_utils.make_instance()
  test_utils.post_server_command(iid, 'bac_guess', ['a', 'b', 'c', 'd'],
                                 error_expected = True)

def test_resend_guess():
  iid = test_utils.make_instance()
  test_utils.post_server_command(iid, 'bac_new_game', [])
  instance = test_utils.get_instance_model(iid)
  guess = instance.bac_solution[::-1]
  score = instance.bac_score
  guesses = instance.bac_guesses_remaining
  response = test_utils.post_server_command(iid, 'bac_guess', guess)
  assert response['contents'] == [guesses - 1, score - 4, 0, 4]
  response = test_utils.post_server_command(iid, 'bac_guess', guess)
  assert response['contents'] == [guesses - 1, score - 4, 0, 4]
  guess = [instance.bac_solution[0]]*4
  response = test_utils.post_server_command(iid, 'bac_guess', guess)
  assert response['contents'] == [guesses - 2, score - 7, 1, 3]
  response = test_utils.post_server_command(iid, 'bac_guess', guess)
  assert response['contents'] == [guesses - 2, score - 7, 1, 3]
  guess = instance.bac_solution
  response = test_utils.post_server_command(iid, 'bac_guess', guess)
  assert response['contents'] == [guesses - 3, score - 7, score - 7, 1, True]
  response = test_utils.post_server_command(iid, 'bac_guess', guess)
  assert response['contents'] == [guesses - 3, score - 7, score - 7, 1, True]
