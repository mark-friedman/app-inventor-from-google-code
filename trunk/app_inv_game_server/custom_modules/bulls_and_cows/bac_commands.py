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
'''
A version of bulls and cows using colors.

At the beginning of a new game a solution sequence of four colors is
randomly chosen from the set of colors. Each color appears at most
once in the solution. The player then makes guesses on the sequence of
colors in the solution. After each guess, the is informed of how many
'cows' and 'bulls' they have in their guess. A 'bull' is when a player
has the correct color in the correct position in their guess. A 'cow'
is when a player has one of the correct colors, but it is in the wrong
position.

Although the solution only includes each color once, a player is
allowed to use the same color more than once in their guess. While
obviously not correct, doing so might give the player information that
they want about the solution.

The player begins with a score such that they will end with a score of
zero if they guess completely wrong every time. After each guess is
made, two points are deducted for each completely wrong color and one
point is deducted for a correct color in the wrong spot (a cow). No
points are deducted for a bull. If a player does not determine the
correct sequence before they run out of guesses they are not awarded a
score.
'''

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from random import sample
from django.utils import simplejson

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
  instance.check_leader(player)
  if len(instance.players) != 1:
    raise ValueError("Only a single player may be in a Bulls and Cows game")

  if 'bac_high_score' not in instance.dynamic_properties():
    instance.bac_high_score = 0
  if 'bac_game_count' not in instance.dynamic_properties():
    instance.bac_game_count = 0

  instance.max_players = 1
  instance.bac_solution = sample(colors, solution_size)
  instance.bac_guesses_remaining = starting_guesses
  instance.bac_score = solution_size * starting_guesses * 2
  instance.bac_last_guess = ['']
  instance.bac_last_reply = ''

  return [instance.bac_guesses_remaining, instance.bac_score,
          instance.bac_high_score, instance.bac_game_count]

def guess_command(instance, player, arguments):
  """ Evaluate a guess and determine the score.

  Args:
    instance: The GameInstance database model for this operation.
    player: The player making the guess. Must be the leader of
      the instance.
    arguments: A list of guessed colors.

  new_game_command must be invoked before a guess can be made.

  Returns:
    If the player has guessed correctly:
      A five element list containing the number of guesses remaining
      at the end, the final score for this game, the high score, a
      boolean of whether or not this game set a new high score and the
      new total number of games completed.

    Otherwise:
      A four element list containing the number of guesses remaining,
      the player's remaining score, the number of bulls for this guess
      and the number of cows for this guess.

  Raises:
    ValueError if the player is not the current instance leader and only
    member of the game.
    ValueError if the player has no guesses remaining.
    ValueError if the guess does not have the correct number of elements.
    ValueError if no game has been started yet.
  """
  instance.check_leader(player)

  if len(arguments) != solution_size:
    raise ValueError("Guess was not the right number of elements.")

  if arguments == instance.bac_last_guess:
    return simplejson.loads(instance.bac_last_reply)

  if ('bac_guesses_remaining' not in instance.dynamic_properties() or
      instance.bac_guesses_remaining == 0):
    raise ValueError("No guesses remaining, please start a new game.")

  return_content = None
  instance.bac_guesses_remaining -= 1
  if arguments == instance.bac_solution:
    guesses = instance.bac_guesses_remaining
    instance.bac_guesses_remaining = 0
    instance.bac_game_count += 1

    new_high_score = False
    if instance.bac_score > instance.bac_high_score:
      new_high_score = True
      instance.bac_high_score = instance.bac_score

    del instance.bac_solution
    return_content = [guesses, instance.bac_score, instance.bac_high_score,
                      instance.bac_game_count, new_high_score]
  else:
    bulls = cows = 0
    for i in xrange(solution_size):
      if arguments[i] == instance.bac_solution[i]:
        bulls += 1
      elif arguments[i] in instance.bac_solution:
        cows += 1

    score_deduction = solution_size * 2 - cows - 2 * bulls
    instance.bac_score -= score_deduction
    return_content = [instance.bac_guesses_remaining, instance.bac_score,
                      bulls, cows]
  instance.bac_last_reply = simplejson.dumps(return_content)
  instance.bac_last_guess = arguments
  return return_content
