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
Functionality for card games. Uses a single deck of cards for and
keeps track of each players hands using a dictionary stored with the
game instance.

The default deck is a standard 52 card deck. Each card is represented
as a two element list with its numerical value (1-13) as the first
element and its suit as the second element. Suits are the strings
'Hearts', 'Spades', 'Clubs' and 'Diamonds'.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

import random
from django.utils import simplejson
from game_server.models.message import Message
from game_server.utils import get_boolean
from google.appengine.ext import db

default_deck = [[n, s] for n in range(14)[1:]
                for s in  ['Hearts','Spades', 'Clubs','Diamonds']]

############################
# Server command functions #
############################

def set_deck_command(instance, player, arguments):
  """ Set the instance's deck to a new list of cards.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player requesting the action.
      For this command, the player must be the current leader of the
      instance.
    arguments: A list of the cards to set the deck to.

  Resets the deck used by card games from a standard 52 card deck to
  the deck specified by the arguments list. A new deck can only be set
  when no other card game methods have been invoked for a particular
  game instance. The deck will remain the same throughout the life of
  the game instance.

  Returns:
    The number of cards in the new deck.

  Raises:
    A ValueError if the requesting player is not the leader of the
    instance.
  """
  instance.check_leader(player)
  return set_deck(instance, arguments)

def deal_cards_command(instance, player, arguments):
  """ Deal cards to players.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player requesting the action.
      The player must be the current leader of the instance.
    arguments: A list of arguments to this command as explained below.

  The arguments list for this command consists of five items in order:
    1: cards_to_deal - The number of cards to deal as an integer.
    2: shuffle_deck - A boolean controlling whether or not the deck
       should be shuffled before the new hands are dealt. If the deck
       is shuffled, all hands are also cleared regardless of the value
       of is_new_hand.
    3: is_new_hand - A boolean indicating whether this is a new hand
       or not.  If it is a new hand, then all hands will be cleared
       before the new cards are dealt. If the deck is shuffled before
       the cards are dealt then the hands are cleared automatically
       and this has no effect.
    4: ignore_empty_deck - Another boolean controlling whether to
       ignore an empty deck or not. If it is true, then cards will be
       dealt until the deck runs out and then this command will return
       successfully. If it is false, an error will occur if the deck
       runs out of cards.
    5: A list of player id's to be dealt to in the order to deal to
       them. Cards will be dealt one at a time to players in the order
       that they appear in this list.

  Cards are dealt to players using the instance's deck according to
  the arguments specified above. The cards are dealt in the order
  determined by the last shuffling. Until a deck is re-shuffled, cards
  will be dealt as if they were removed from the top of the deck and
  given to the player permanently.

  Returns:
    The hand of the requesting player after cards are dealt.

  Raises:
    An IndexError if the deck runs out of cards and empty deck errors
    are not being ignored.
    A ValueError if any of the player id's in the list of players to
    deal to are not in the game instance.
    A ValueError if the requesting player is not the leader of the
    instance.
  """
  instance.check_leader(player)
  cards_to_deal = int(arguments[0])
  shuffle = get_boolean(arguments[1])
  if shuffle:
    shuffle_deck(instance)
  is_new_hand = get_boolean(arguments[2])
  ignore_empty_deck = get_boolean(arguments[3])
  hands = deal_cards(instance, cards_to_deal, is_new_hand, ignore_empty_deck,
                     arguments[4])
  return hands[player]

def draw_cards_command(instance, player, arguments):
  """ Draw cards from the deck and put them into the calling player's hand.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player requesting the action.
    arguments: A list of arguments to this command as explained below.

  The arguments list for this command consists of two items in order:
    1: cards_to_draw - The number of cards to attempt to draw.
    2: ignore_empty_deck - A boolean controlling whether to ignore an
       empty deck or not. If it is true, cards can be drawn until the
       deck runs out and then this command will return
       successfully. If it is false, an error will occur if the deck
       runs out of cards and no changes will be made to the hand of
       the player.

  Returns:
    The hand of the player after drawing the new cards.

  Raises:
    An IndexError if the deck runs out of cards and empty deck errors
    are not being ignored.
    ValueError if the requesting player is not in the instance.
  """
  cards_to_draw = int(arguments[0])
  ignore_empty_deck = get_boolean(arguments[1])
  return draw_cards(instance, player, cards_to_draw, ignore_empty_deck)

def discard_command(instance, player, arguments):
  """ Remove the specified cards from the calling player's hand.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player requesting the action.
    arguments: A list of cards to discard.

  Discarded cards are removed from a player's hand permanently. They
  are not re-added to the deck of cards to be dealt to other
  players. However, once a deck is shuffled, all cards become
  available again including any that have been discarded.

  If a player tries to discard a card that is not in their hand on the
  server, the request to discard that particular card is ignored, but
  the execution of the command continues.

  Returns:
    The current hand of the requesting player.
  """
  return discard(instance, player, arguments)

def pass_cards_to_player_command(instance, player, arguments):
  """ Remove cards from the calling player's hand and add them to another hand.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player requesting the action.
    arguments: A list of two items. The first item is the email
      address of the player to pass the cards to and the second is a
      list of cards to pass to them.

  Raises:
    A ValueError if the player to pass the cards to is not in the game
    instance.

  """
  hands = get_hand_dictionary(instance)
  to_player = instance.check_player(arguments[0])
  return pass_cards(instance, player, to_player, arguments[1])

def get_cards_remaining_command(instance, player, arguments = None):
  """ Return the number of cards left in this deck to deal.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player requesting the action.
    arguments: Not used, can be any value.

  Returns:
    The number of cards that can still be dealt before the deck is
    empty.  If the deck has not been set or no cards have been dealt
    (in the case that the default deck is being used), returns -1.
  """
  return cards_left(instance)

###########
# Helpers #
###########

def get_deck(instance):
  """ Return the deck for this instance.

  Args:
    instance: The GameInstance database model for this operation.

  Returns:
    The current deck for this instance. If no deck exists, returns the
    default deck, unshuffled.
  """
  if 'crd_deck_index' not in instance.dynamic_properties():
    instance.crd_deck_index = 0
  if 'crd_deck' not in instance.dynamic_properties():
    instance.crd_deck = [simplejson.dumps(card) for card in default_deck]
  return instance.crd_deck

def set_deck(instance, deck):
  """ Set the deck for this instance to a new one.

  Args:
    instance: The GameInstance database model for this operation.
    deck: A list of cards to set as a new deck.

  Returns:
    The number of cards in the new deck.

  Raises:
    AttributeError if a deck has already been created for this
    instance.
  """
  if 'crd_deck' in instance.dynamic_properties():
    raise AttributeError('Deck can only be set as the first operation in '
                         'a card game.')
  instance.crd_deck =[simplejson.dumps(card) for card in deck]
  instance.crd_deck_index = 0
  return len(instance.crd_deck)

def get_hand_dictionary(instance):
  """ Return a dictionary with the hands of each player in the instance.

  Args:
    instance: The GameInstance database model for this operation.

  Returns:
    A dictionary with a list for each player in the game. Each
    player's list will include the cards currently in their hand. Keys
    in the dictionary are the email addresses of players.
  """
  if 'crd_hands' not in instance.dynamic_properties():
    return get_empty_hand_dictionary(instance)
  else:
    return simplejson.loads(instance.crd_hands)

def get_empty_hand_dictionary(instance):
  """ Return a dictionary with an empty hand for each player in the instance.

  Args:
    instance: The GameInstance database model for this operation.

  Returns:
    A dictionary with an empty list for each player in the game. Keys
    in the dictionary are the email addresses of players.
  """
  hands = {}
  for player in instance.players:
    hands[player] = []
  return hands

def set_hand_dictionary(instance, hands, send_messages = True):
  """ Set the hands of all players and send new hand messages.

  Args:
    instance: The GameInstance database model for this operation.
    hands: A dictionary containing the hand of each player in the
    game.
    send_messages: Whether or not to send a message to each player
      with their new hand.

  Stores the hands dictionary in the game instance. If send_messages
  is True, this will also send a new 'crd_hand' message to each player
  with their new hand.
  """
  if send_messages:
    message_list = []
    for player in instance.players:
      message_list.append(instance.create_message(player, 'crd_hand',
                                                  player, hands[player]))
    db.put(message_list)
  instance.crd_hands = db.Text(simplejson.dumps(hands))

def get_player_hand(instance, player):
  """ Get the hand of a single player in an instance.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player.

  Returns:
    The list of cards that the player has or an empty list if they
    do not have a hand.

  Raises:
    ValueError if the player is not in the instance.
  """
  player = instance.check_player(player)
  hands = get_hand_dictionary(instance)
  return hands.get(player, [])

def set_player_hand(instance, player, hand, send_message = True):
  """ Set the hand of a single player in an instance.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player.
    hand: The new hand of the player.
    send_message: Whether to send player a 'crd_hand' message
      with their new hand.

  Stores the new hands dictionary with the updated hand for player.
  If send_message is True, a message will be sent to player with
  their new hand.

  Raises:
    ValueError if the player is not in the instance.
  """
  player = instance.check_player(player)
  hands = get_hand_dictionary(instance)
  hands[player] = hand
  set_hand_dictionary(instance, hands, send_messages = False)
  if send_message:
    instance.create_message(player, 'crd_hand', player, hand).put()

def get_next_card(instance):
  """ Return the card in the deck.

  Args:
    instance: The GameInstance database model for this operation.

  Returns:
    The Python representation of the next card in the deck. Because
    cards are stored as JSON strings they are first decoded before
    being returned.

  Raises:
    ValueError if the JSON decoding fails.
    IndexError if the deck has run out of cards.
  """

  if cards_left(instance) == 0:
    raise IndexError('Deck is empty')
  card = simplejson.loads(get_deck(instance)[instance.crd_deck_index])
  instance.crd_deck_index = instance.crd_deck_index + 1
  return card

def shuffle_deck(instance):
  """ Shuffle the deck and reset all hands.

  Args:
    instance: The GameInstance database model for this operation.

  Shuffles all cards in the original deck and makes them available to
  be dealt or drawn again. Also clears all players hands.

  Returns:
    The number of cards in the deck.
  """
  deck = get_deck(instance)
  random.shuffle(deck)
  instance.crd_deck_index = 0
  instance.crd_deck = deck

  set_hand_dictionary(instance, get_empty_hand_dictionary(instance))
  return len(instance.crd_deck)

def pass_cards(instance, from_player, to_player, cards):
  """ Pass cards from one player to another.

  Args:
    instance: The GameInstance database model for this operation.
    from_player: Email address of the player who is passing the cards.
    to_player: Email address of the player who is receiving the cards.
    cards: A list of cards to pass.

  Searches the hand of from_player for each card in cards and if it
  is present, transfers it to_player's hand. If a card is not present,
  it is ignored.

  Returns:
    The hand of from_player after passing the cards.
  """
  hands = get_hand_dictionary(instance)
  from_player = instance.check_player(from_player)
  to_player = instance.check_player(to_player)

  for card in cards:
    try:
      hands[from_player].remove(card)
      hands[to_player].append(card)
    except ValueError:
      pass
  set_hand_dictionary(instance, hands)
  return hands[from_player]

def discard(instance, player, cards, send_message = True):
  """ Remove the specified cards from player's hand.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player to discard cards from.
    cards: The cards to be discarded.
    send_message: Whether to send player a 'crd_hand' message
      with their new hand.

  Discarded cards are removed from a player's hand permanently. They
  are not re-added to the deck of cards to be dealt to other
  players. However, once a deck is shuffled, all cards become
  available again including any that have been discarded.

  If a player tries to discard a card that is not in their hand on the
  server, the request to discard that particular card is ignored, but
  the execution of the command continues.

  Returns:
    The hand of player after discarding the cards.

  Raises:
    ValueError if the player is not in the instance.
  """
  hand = get_player_hand(instance, player)
  for card in cards:
    try:
      hand.remove(card)
    except ValueError:
      pass
  set_player_hand(instance, player, hand, send_message)
  return hand

def deal_cards(instance, cards_to_deal, is_new_hand, ignore_empty_deck,
               deal_to):
  """ Deal cards to players.

  Args:
    instance: The GameInstance database model for this operation.

    cards_to_deal: The number of cards to deal as an integer.
    is_new_hand: A boolean indicating whether this is a new hand or
      not.  If it is a new hand, then all hands will be cleared before
      the new cards are dealt. If the deck is shuffled before the
      cards are dealt then the hands are cleared automatically and
      this has no effect.
    ignore_empty_deck: Another boolean controlling whether to ignore
      an empty deck or not. If it is true, then cards will be dealt
      until the deck runs out and then this command will return
      successfully. If it is false, an error will occur if the deck
      runs out of cards.
    deal_to: A list of player id's to be dealt to in the order to deal
      to them.  Cards will be dealt one at a time to players in the
      order that they appear in this list.

  The cards are dealt in the order determined by the last
  shuffling. Until a deck is re-shuffled, cards will be dealt as if
  they were removed from the top of the deck and given to the player
  permanently.

  Returns:
    The hand of the requesting player after cards are dealt.

  Raises:
    ValueError if a player in deal_to is not in the instance.
    IndexError if the deck runs out of cards and ignore_empty_deck is
    not True.
  """
  hands = {}
  if not is_new_hand:
    hands = get_hand_dictionary(instance)

  if cards_to_deal:
    deal_to = [instance.check_player(pid) for pid in deal_to]
    for player in deal_to:
      hands.setdefault(player, [])
    try:
      for i in xrange(cards_to_deal):
        for player in deal_to:
          hands[player].append(get_next_card(instance))
    except IndexError:
      if not ignore_empty_deck:
        raise

  set_hand_dictionary(instance, hands)
  return hands

def draw_cards(instance, player, cards_to_draw,
               ignore_empty_deck = True, send_message = True):
  """ Draw cards from the deck and put them into player's hand.

  Args:
    instance: The GameInstance database model for this operation.
    player: The email address of the player to give the cards to.
    cards_to_draw: The number of cards to draw from the deck.
    ignore_empty_deck - A boolean controlling whether to ignore an
       empty deck or not. If it is true, cards can be drawn until the
       deck runs out and then this command will return
       successfully. If it is false, an error will occur if the deck
       runs out of cards and no changes will be made to the hand of
       the player.
    send_message: Whether to send player a 'crd_hand' message
      with their new hand.

  Returns:
    The hand of the requesting player after they have drawn their
    cards.

  Raises:
    ValueError if player is not in the game instance.
    IndexError if the deck runs out of cards and ignore_empty_deck is
    not True.
  """
  hand = get_player_hand(instance, player)
  try:
    for i in xrange(cards_to_draw):
      hand.append(get_next_card(instance))
  except IndexError:
    if not ignore_empty_deck:
      raise
  set_player_hand(instance, player, hand, send_message)
  return hand

def cards_left(instance):
  """ Return the number of cards left to deal before a shuffle is required.

  Args:
    instance: The GameInstance database model for this operation.

  Returns
    The number of cards that can still be dealt before the deck is
    empty. If the deck has not been set or no cards have been dealt
    (in the case that the default deck is being used), returns -1.
  """
  if 'crd_deck' not in instance.dynamic_properties():
    return -1
  return len(instance.crd_deck) - instance.crd_deck_index
