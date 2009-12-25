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
from game_server.models import Game
from game_server.models import GameInstance
from game_server.server import application
from game_server.tests import test_utils

gid = 'test_gid'
firstpid = 'test@test.com'

def setUp():
  test_utils.clear_data_store()

def test_game_creation():
  game = Game.get_or_insert(key_name = gid)
  assert game.instance_count == 0
  assert len(game.get_public_instances_query().fetch(1)) == 0
  
def test_instance_creation():
  iid = 'instance_create_iid'
  player = 'test@test.com'
  game = Game.get_or_insert(key_name = gid)
  instance = GameInstance(parent = game,
                          key_name = iid,
                          players = [player],
                          leader = player)
  assert not instance.full
  assert not instance.public
  assert instance.max_players == 0
  assert instance.scoreboard == '{}'

def test_instance_full():
  iid = 'instance_full_iid'
  player = 'test@test.com'
  game = Game.get_or_insert(key_name = gid)
  instance = GameInstance(parent = game,
                          key_name = iid,
                          players = [player],
                          leader = player)
  assert not instance.full
  instance.max_players = 1
  assert not instance.full
  instance.put()
  assert instance.full
  instance.max_players = 2
  instance.put()
  assert not instance.full
  instance.players = [player, 'test2@test.com']
  instance.put()
  assert instance.full
  instance.max_players = 0
  instance.put()
  assert not instance.full

def test_instance_public():
  iid = 'instance_public_iid'
  player = 'test@test.com'
  game = Game.get_or_insert(key_name = 'public_game')
  instance = GameInstance(parent = game,
                          key_name = iid,
                          players = [player],
                          leader = player)
  instance.put()
  assert instance not in game.get_public_instances_query().fetch(1000)
  instance.public = True
  instance.put()
  public_game = game.get_public_instances_query().fetch(1)[0]
  assert public_game.to_dictionary() == instance.to_dictionary()
  instance.public = False
  instance.put()
  assert len(game.get_public_instances_query().fetch(1000)) == 0


  
