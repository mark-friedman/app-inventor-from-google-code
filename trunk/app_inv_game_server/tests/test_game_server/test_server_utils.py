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

"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

import google.appengine.api
import unittest
from game_server import utils

players = ['test@test.com', '"Bob Jones" <test2@test.com>', '<test3@test.com>']

def test_check_playerid():
  assert utils.check_playerid(players[0]) == 'test@test.com'
  assert utils.check_playerid(players[1]) == 'test2@test.com'
  assert utils.check_playerid(players[2]) == 'test3@test.com'

def test_get_game_that_does_not_exist():
  model = utils.get_game_model('test')
  assert not model

def test_get_boolean():
  assert utils.get_boolean('tRuE') == True
  assert utils.get_boolean('TRUE') == True
  assert utils.get_boolean('true') == True
  assert utils.get_boolean('fAlSe') == False
  assert utils.get_boolean('false') == False
  assert utils.get_boolean('FALSE') == False
  try:
    utils.get_boolean('true that')
    assert False
  except ValueError:
    pass
  assert utils.get_boolean(True) == True
  assert utils.get_boolean(False) == False
