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
from datetime import datetime
from game_server.models.game import Game
from game_server.models.game_instance import GameInstance
from game_server.models.message import Message
from google.appengine.ext import db
from tests import test_utils

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

def test_delete_messages():
  iid = 'instance_messages_iid'
  player = 'test@test.com'
  game = Game.get_or_insert(key_name = gid)
  instance = GameInstance.get_or_insert(parent = game,
                                        key_name = iid,
                                        players = [player],
                                        leader = player)
  for i in xrange(50):
    message = Message(parent = instance,
                      sender = player,
                      msg_type = 'blah',
                      recipient = player,
                      content = '%d' % i)
    message.put()
  messages = Message.all(keys_only = True).ancestor(instance.key()).fetch(1000)
  assert len(messages) == 50

  instance.delete_messages('blah')
  messages = Message.all(keys_only = True).ancestor(instance.key()).fetch(1000)
  assert len(messages) == 0
