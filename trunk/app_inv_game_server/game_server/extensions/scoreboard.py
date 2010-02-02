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
Provides methods to use a scoreboard with GameInstance models.

All scores are stored as integers with the convention that higher
numbers are better.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

import operator
from django.utils import simplejson
from google.appengine.ext import db

############################
# Server command functions #
############################

def get_scoreboard_command(instance, player, arguments = None):
  """ Get the current scoreboard.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player requesting this action.
    arguments: Not used, can be any value.

  Returns:
    The complete scoreboard as a list of [score, email] lists for
    each player in the game. The scoreboard is sorted with the highest
    score first.
  """
  return format_scoreboard_for_app_inventor(get_scoreboard(instance))

def get_score_command(instance, player, arguments):
  """ Set the score of a single player.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player requesting this action.
    arguments: A one item list containing the player id of the
      player to get the score of.

  Returns:
    The score of the requested player.

  Raises:
    ValueError if the player in arguments is not in the game.
  """
  get_score_player = instance.check_player(arguments[0])
  return get_score(instance, get_score_player)

def set_score_command(instance, player, arguments):
  """ Set a player's score to a new value.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player to set the score of.
    arguments: A list of two items. The first item is the player id
      of the player who's score is to be set. The second item is the
      integer to set that player's score to.

  Returns:
    The complete scoreboard after setting the new score value.

  Raises:
    ValueError if the specified player is not in the instance.
  """
  player = instance.check_player(arguments[0])
  new_score = arguments[1]
  board = set_score(instance, player, new_score)
  return format_scoreboard_for_app_inventor(board)


def add_to_score_command(instance, player, arguments):
  """ Change a player's score by an integer amount.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player to add points to.
    arguments: A list of two items. The first item is the player id
      of the player who's score is to be set. The second item is the
      integer amount to change that player's score by. This value can
      be positive or negative.

  In order for this operation to work correctly scores must be
  represented in the scoreboard as single integer items.

  Returns:
    The complete scoreboard after adding to player's score.

  Raises:
    ValueError if the specified player is not in the instance.
    ValueError if the specified score cannot parse correctly.
  """
  player = instance.check_player(arguments[0])
  delta = int(arguments[1])
  board = add_to_score(instance, player, delta)
  return format_scoreboard_for_app_inventor(board)

def clear_scoreboard_command(instance, player, arguments = None):
  """ Reset all scores to 0.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player requesting this action.
      For this command, the player must be the current leader of the
      instance.
    arguments: Not used, can be any value.

  Returns:
    An empty scoreboard with a score of 0 for each player.

  Raises:
    ValueError if player is not the leader of this instance.
  """
  instance.check_leader(player)
  instance.scoreboard = '{}'
  return get_scoreboard_command(instance, player, arguments)


###########
# Helpers #
###########

def get_score(instance, player):
  """ Get a player's score.

  Args:
    instance: The instance to get the scoreboard from.
    player: The player to check the score of.

  Returns:
    The players score.

  Raises:
    ValueError if the player is not in the instance.
  """
  player = instance.check_player(player)
  board = get_scoreboard(instance)
  return board[player]

def set_score(instance, player, new_score):
  """ Set a player's score.

  Args:
    instance: The game instance to modify the scoreboard of.
    player: The player to set the score of.
    new_score: An integer to set their score to.

  Returns:
    The scoreboard as a dictionary after setting a new value for
    player's score.

  Raises:
    ValueError if the player is not in the instance.
  """
  player = instance.check_player(player)
  scoreboard = get_scoreboard(instance)
  scoreboard[player] = new_score
  instance.scoreboard = simplejson.dumps(scoreboard)
  return scoreboard

def add_to_score(instance, player, delta):
  """ Change a player's score by delta.

  Args:
    instance: The game instance to modify the scoreboard of.
    player: The player to change the score of.
    delta: The integer amount to change player's score by (can be
    negative).

    In order for this operation to work correctly scores must be
    represented in the scoreboard as single integer items.

  Returns:
    The scoreboard as a dictionary after modifying player's score.
  """
  player = instance.check_player(player)
  scoreboard = get_scoreboard(instance)
  if player in scoreboard:
    scoreboard[player] += delta
  else:
    scoreboard[player] = delta
  instance.scoreboard = db.Text(simplejson.dumps(scoreboard))
  return scoreboard

def get_scoreboard(instance):
  """ Get a dictionary of the scoreboard for the specified instance.

  Args:
    instance: The instance to get the scoreboard from.

  Returns:
    A dictionary with a score entry for each player in the
    instance. If no score was previously present, a value of
    0 is entered.
  """
  board = None
  if 'scoreboard' not in instance.dynamic_properties():
    board = {}
  else:
    board = simplejson.loads(instance.scoreboard)
  for player in instance.players:
    if not board.has_key(player):
      board[player] = 0
  return board

def format_scoreboard_for_app_inventor(board):
  """ Return a scoreboard suitable to return to App Inventor.

  Args:
    board: The dictionary of scores for all players in the game.

  Returns:
    A list of [score, player email] lists ordered by highest score.
  """
  board_list = [[v,k] for k, v in board.items()]
  board_list.sort(key = operator.itemgetter(0), reverse = True)
  return board_list
