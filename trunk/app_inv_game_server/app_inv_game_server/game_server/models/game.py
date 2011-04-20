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
The Game database model class and associated methods.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from google.appengine.ext import db
from game_instance import GameInstance

class Game(db.Model):
  """ A model for a game type.

  A Game is the parent object of GameInstance objects. Each Game
  object should correspond to a type of game. Class methods are
  available that provide queries to discover GameInstance objects
  with this parent.

  The key_name of a Game should be the game's name.

  Attributes:
    instance_count: The number of instances that have been made with
      this Game as their parent. This number is managed manually.
  """
  instance_count = db.IntegerProperty(default=0)

  def get_new_instance(self, prefix, player):
    """ Create a new GameInstance and return its model.

    Args:
      prefix: A string used as the beginning of the instance id.
      player: The email address of the player.

    When this returns, neither this Game model or the new
    GameInstance have been put() in the database. If the GameInstance
    should persist, both models need to be put().

    Returns:
      A GameInstance object with a unique instance id beginning with
      prefix and player as the leader and sole member of the
      instance.
    """
    prefix = prefix.replace(' ', '')
    new_iid = prefix
    self.instance_count += 1
    new_index = self.instance_count
    while GameInstance.get_by_key_name(new_iid, parent=self) is not None:
      new_index += 1
      new_iid = prefix + str(new_index)
    instance = GameInstance(parent = self, key_name = new_iid,
                          players = [player], leader = player)
    return instance

  def get_public_instances_query(self, keys_only = False):
    """ Return a query object for public instances of this game.

    Args:
      keys_only (optional): Whether this database query should return
        only keys, or entire models.

    Returns:
      A query object of all public game instances that are not full
      in order of creation time from oldest to newest. Any instance
      returned by this query should be able to be joined by any
      player at the time the results are fetched.
    """
    query = GameInstance.all(keys_only = keys_only)
    query.filter("public =", True)
    query.filter("full =", False)
    query.ancestor(self.key())
    query.order('-date')
    return query

  def get_invited_instance_keys_query(self, player):
    """ Return a query object for instances a player has been invited to.

    Args:
      player: The email address of the player.

    Returns:
      A query object of all game instances that player has been
      invited to and that are not full in order of creation time from
      oldest to newest. Any instance returned by this query should be
      able to be joined by the player at the time the results are
      fetched.
    """
    query = GameInstance.all(keys_only = True)
    query.filter("invited =", player)
    query.filter("full =", False)
    query.ancestor(self.key())
    query.order('-date')
    return query

  def get_joined_instance_keys_query(self, player):
    """ Return a query object for instances a player has already joined.

    Args:
      player: The email address of the player.

    Returns:
      A query object of all game instances that player has joined in
      order of creation time from oldest to newest.
    """
    query = GameInstance.all(keys_only = True)
    query.filter("players =", player)
    query.ancestor(self.key())
    query.order('-date')
    return query
