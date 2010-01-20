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
A set of server commands to implement Androids to Androids.

Androids to Androids is a card game played by at least three
players. The first leader of the game is the creator of the game
instance. The game proceeds in rounds with the winner of each round
becoming the leader of the next round. To start the game, each player
is dealt seven cards with nouns on them. These cards comprise their
hand.

At the beginning of each round, an adjective or characteristic is
chosen at random and sent to each player. Every player except the
leader will then choose a card from their hand to submit for the
round. Upon submission their hand will be replenished with another
card so that they always have seven cards in their hand.

The leader will then choose a single noun card from those submitted by
the other players in response to the characteristic.  The leader can
use any criteria they wish to select the card that should win the
round, however, they are not allowed to know the identity of the
person that submits each card.

Once a winner is chosen, a new round is started with the previous
winner as the new leader. Play continues in this way until one of the
players reaches a predetermined winning score and is declared the
winner.

Each command returns information that is immediately useful to the player
who requested the command. In addition, any changes to their hand or
the set of cards players have submitted will be sent to them via message
so that they can easily recover state if they lose their active session
in the game.

Submitting cards and ending turns both require that the player submit
the round number that they intend for that action to apply to. If that
number does not match the current round the action will be ignored and
the command will return information to allow that player to get back up
to date with the game.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

import random
import decks
from game_server.extensions import scoreboard
from game_server.extensions import card_game
from google.appengine.ext import db
from django.utils import simplejson

hand_size = 7
winning_score = 5
min_players = 3

#################
# Game Commands #
#################

def new_game_command(instance, player, arguments = None):
  """ Start a new game of Androids to Androids.

  Args:
    instance: The GameInstance database model for this operation.
    player: The player starting the game. Must be the current leader
      of instance.
    arguments: Not used, can be any value.

  Closes the game to new players, deals a new hand to each player and
  selects a new characteristic card to begin round 1. Sends a new game
  message to all players with the starting card and the empty scoreboard.

  Each player will also receive a message of type crd_hand that contains
  all of the cards dealt to them.

  Returns:
    A three item list consisting of the new characteristic card for
    this turn, the current (empty) scoreboard, and the player's current
    hand.

  Raises:
    ValueError if an Androids to Androids game is already in progress,
    if player is not the current leader of the game or if there are not
    enough players in the game to begin.
  """
  player = instance.check_leader(player)

  if 'ata_round' in instance.dynamic_properties():
    raise ValueError("An Androids to Androids game is already in progress.")

  if len(instance.players) < min_players:
    raise ValueError("Androids to Androids requires at least %d players."
                     % min_players)

  instance.public = False
  instance.max_players = len(instance.players)
  try:
    card_game.set_deck(instance, decks.noun_cards)
  except AttributeError:
    pass
  card_game.shuffle_deck(instance)
  hands = card_game.deal_cards(instance, hand_size, True, False,
                               instance.players)

  instance.ata_round = 0
  setup_new_round(instance)
  board = scoreboard.clear_scoreboard_command(instance, player)
  instance.create_message(instance.leader, 'ata_new_game', '',
                          [instance.ata_char_card, board]).put()

  return [instance.ata_char_card, board, hands[player]]

def submit_card_command(instance, player, arguments):
  """ Submit a noun card for the current round.

  Args:
    instance: The GameInstance database model for this operation.
    player: The player submitting the card. Cannot be the leader.
    arguments: A two item list consisting of the round to submit this
      card to and the card itself.

  Removes the indicated card from the player's hand and adds it
  to this rounds submissions. The current submissions are sent via
  message to all players.

  Player's hand will be dealt another card after removing the submitted
  one. A message will be sent to player with the contents of the hand
  and the new hand will be included in the return value of this command.

  Returns:
    If the submission is for the correct round, returns a three item
    list consisting of the current round, the players new hand and
    a list of the submissions made so far by other players in this
    round.

    If the submission is for the wrong round, a three item list with
    the string 'wrong_round' as its first element will be returned.
    The next two elements are the current round and the current
    characteristic card to respond to.

  Raises:
    ValueError if player is the leader. The leader is not allowed to
    submit cards.
  """
  if int(arguments[0]) != instance.ata_round:
    return ['wrong_round', instance.ata_round, instance.ata_char_card]

  if player == instance.leader:
    raise ValueError("The leader may not submit a card.")

  submission = arguments[1]
  submissions = set_submission(instance, player, submission).keys()
  instance.create_message(player, 'ata_submissions', '',
                          [instance.ata_round, submissions]).put()

  card_game.discard(instance, player, [submission])
  hand = card_game.draw_cards(instance, player, 1)
  return [instance.ata_round, hand, submissions]

def end_turn_command(instance, player, arguments):
  """ End the current turn and start a new one.

  Args:
    instance: The GameInstance database model for this operation.
    player: The player submitting the card. Must be the current leader.
    arguments: A two item list consisting of the round number to end
      and the selected winning card.

  Ends the current turn and adds 1 point to the score of the player
  who submitted the winning card. If that player has then reached the
  winning score, an 'ata_game_over' message will be sent to all players.
  The game over message content will be a four item list consisting of
  the current round number, the winner's email, the winning card and
  the final scoreboard.

  Otherwise, sends an 'ata_new_round' message to all players. The new round
  message contents will be a five item list with the round number, the
  new characteristic card, the previous round winner, the winning card
  and the current scoreboard.

  Returns:
    If the command is for the wrong round, a three item list with
    the string 'wrong_round' as its first element will be returned.
    The next two elements are the current round and the current
    characteristic card to respond to.

    Otherwise, returns the content of whichever message was sent to
    all players as described above.
  Raises:
    ValueError if player is not the leader.
    KeyError if no player has submitted the winning card.
  """
  if int(arguments[0]) != instance.ata_round:
    return ['wrong_round', instance.ata_round, instance.ata_char_card]

  instance.check_leader(player)
  card = arguments[1]
  try:
    winner = get_submissions_dict(instance)[card]
  except KeyError:
    raise KeyError('No player has submitted the card %s.' % card)
  board = scoreboard.add_to_score(instance, winner, 1)

  # Check to see if anyone has won
  instance.leader = winner
  if board[winner] == winning_score:
    return end_game(instance, card)

  setup_new_round(instance)
  return_scoreboard = scoreboard.format_scoreboard_for_app_inventor(board)
  content = [instance.ata_round, instance.ata_char_card, winner, card,
             return_scoreboard]
  instance.create_message(instance.leader, 'ata_new_round', '', content).put()
  return content

###########
# Helpers #
###########

def end_game(instance, winning_card):
  """ End the current game and inform all players of the winner.

  Args:
    instance: The GameInstance database model for this operation.
    winning_card: The card chosen as the winner of the final round.

  Sends an 'ata_game_over' message to all players with a four item
  list as its contents. The list contains the final round number, the
  winning player's email, the winning card and the final scoreboard.

  Deletes the ata_round, ata_char_card and ata_submissions properties
  from the GameInstance database model to allow for a new game to be
  player in this same instance with the previous winner as the new leader.

  Returns:
    The content of the message sent to all players.
  """
  content = [instance.ata_round, instance.leader, winning_card,
             scoreboard.get_scoreboard_command(instance, instance.leader)]
  instance.create_message(instance.leader, 'ata_game_over', '', content).put()

  del instance.ata_round
  del instance.ata_char_card
  del instance.ata_submissions
  return content

def setup_new_round(instance):
  """ Update the round number, char card and submissions for a new round.

  Args:
    instance: The GameInstance database model for this operation.

  Increments ata_round, clears the submissions dictionary and sets
  ata_char_card to a new value from the list of characteristic cards.
  """
  instance.ata_round += 1
  instance.ata_submissions = db.Text('{}')

  new_card = random.choice(decks.characteristic_cards)
  if 'ata_char_card' in instance.dynamic_properties():
    while instance.ata_char_card == new_card:
      new_card = random.choice(decks.characteristic_cards)
  instance.ata_char_card = new_card

def get_submissions_dict(instance):
  """ Return a Python dictionary that maps cards to players.

  Args:
    instance: The GameInstance database model for this operation.

  Returns:
    A Python dictionary of cards to players for all cards
    submitted so far during this round.
  """
  return simplejson.loads(instance.ata_submissions)

def set_submission(instance, player, card):
  """ Records the submission of card as coming from player.

  Args:
    instance: The GameInstance database model for this operation.
    player: The player submitting the card.
    card: The card to submit.

  Returns:
    A Python dictionary of cards to players for all cards
    submitted so far during this round.
  """
  submissions = get_submissions_dict(instance)
  submissions[card] = player
  instance.ata_submissions = simplejson.dumps(submissions)
  return submissions
