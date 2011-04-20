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
A version of bulls and cows using colors.

At the beginning of a new game a solution sequence of four colors is
randomly chosen from the set of colors. Each color appears at most
once in the solution. The player then makes guesses on the sequence
of colors in the solution. After each guess, they are informed of how
many 'cows' and 'bulls' they have in their guess. A 'bull' is when a
player has the correct color in the correct position in their guess.A
'cow' is when a player has one of the correct colors, but it is in
the wrong position.

Although the solution only includes each color once, a player is
allowed to use the same color more than once in their guess. While
obviously not correct, doing so might give the player information
that they want about the solution.

The player begins with a score such that they will end with a score
of zero if they guess completely wrong every time. After each guess
is made, two points are deducted for each completely wrong color and
one point is deducted for a correct color in the wrong spot (a
cow). No points are deducted for a bull. If a player does not
determine the correct sequence before they run out of guesses they
are not awarded a score.  """

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from random import sample
from django.utils import simplejson
from game_server.extensions import scoreboard
from game_server.models.message import Message
from google.appengine.ext import db
from google.appengine.ext.db import Key

starting_guesses = 12
solution_size = 4
colors = ['Blue', 'Green', 'Orange', 'Red', 'Yellow', 'Pink']

def new_game_command(instance, player, arguments = None):
  """ Start a new game and reset any game in progress.

  Args:
    instance: The GameInstance database model for this operation.
    player: The player starting a new game. Must be the only player
      in the instance.
    arguments: Not used, can be any value.

  Returns:
    A list containing the number of guesses remaining, the starting
    score of the player, the player's historical high score and the
    number of games completed in the past.

  Raises:
    ValueError if there is more than 1 player in the instance
    or the player is not the current leader.
  """
  old_games = instance.get_messages_query('bac_game', player,
                                          sender = player,
                                          keys_only = True)
  db.delete(old_games)

  score = scoreboard.get_score(instance, player)
  if (score == 0):
    # Score is [high score, total score, games played]
    score = [0, 0, 0]
    scoreboard.set_score(instance, player, score)

  game = Message(parent = instance, sender = player,
                 msg_type = 'bac_game', recipient = player)
  game.bac_solution = sample(colors, solution_size)
  game.bac_guesses_remaining = starting_guesses
  game.bac_score = solution_size * starting_guesses * 2
  game.bac_last_guess = ['']
  game.bac_last_reply = ''
  game.put()

  return [game.bac_guesses_remaining, game.bac_score, score,
          game.key().id()]

def guess_command(instance, player, arguments):
  """ Evaluate a guess and determine the score.

  Args:
    instance: The GameInstance database model for this operation.
    player: The player making the guess. Must be the leader of
      the instance.
    arguments: A two element list containg the game id and a second
      list with the guessed colors.

  new_game_command must be invoked before a guess can be made.

  Returns:
    If the player has guessed correctly:
      A two element list containg a score list and a boolean of
      whether or not this game set a new high score. The score list is
      a three element list containing the player's high score, their
      total score and their total number of games played.

    Otherwise:
      A four element list containing the player's remaining score, the
      number of guesses remaining, the number of bulls for this guess
      and the number of cows for this guess.

  Raises:
    ValueError if the player is not the current instance leader and
    only member of the game.
    ValueError if the player has no guesses remaining.
    ValueError if the guess does not have the correct number of
    elements.
    ValueError if no game has been started yet.
  """
  guess = arguments[1]
  if len(guess) != solution_size:
    raise ValueError("Guess was not the right number of elements.")

  game = db.get(Key.from_path('Message', int(arguments[0]),
                              parent = instance.key()))

  if game is None:
    raise ValueError("Game not found. Please start a new game.")
  if game.sender != player:
    raise ValueError("This is not your game. Please start a new game.")

  if guess == game.bac_last_guess:
    return simplejson.loads(game.bac_last_reply)

  if game.bac_guesses_remaining == 0:
    raise ValueError("No turns left, please start a new game.")

  return_content = None

  if guess == game.bac_solution:
    game.bac_guesses_remaining = 0
    new_high_score = False
    score = scoreboard.get_score(instance, player)
    if game.bac_score > score[0]:
      new_high_score = True
      score[0] = game.bac_score
    score[1] = score[1] + game.bac_score
    score[2] = score[2] + 1
    scoreboard.set_score(instance, player, score)
    return_content = [score, new_high_score]
  else:
    game.bac_guesses_remaining -= 1
    bulls = cows = 0
    for i in xrange(solution_size):
      if guess[i] == game.bac_solution[i]:
        bulls += 1
      elif guess[i] in game.bac_solution:
        cows += 1

    score_deduction = solution_size * 2 - cows - 2 * bulls
    game.bac_score -= score_deduction
    return_content = [game.bac_guesses_remaining, game.bac_score,
                      bulls, cows]
  game.bac_last_reply = simplejson.dumps(return_content)
  game.bac_last_guess = guess
  game.put()
  return return_content
