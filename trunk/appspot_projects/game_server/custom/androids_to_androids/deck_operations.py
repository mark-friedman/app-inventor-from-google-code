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

import random
from decks import noun_cards
from decks import characteristic_cards
from game_server import models
from game_server import utils
from game_server import server_commands
from google.appengine.ext import db
from django.utils import simplejson

hand_size = 7
winning_score = 5
min_players = 3
message_types = ['ata_noun_card', 'ata_player_submission', 'ata_char_card', 
                 'ata_new_round', 'ata_game_over']

def new_androids_to_androids_game(instance, pid, arguments):
  if pid != instance.leader:
    raise ValueError("Only the current leader (%s) can start a new game."
                     % instance.leader)

  if len(instance.players) < min_players:
    raise ValueError("Androids to Androids requires at least %d players."
                     % min_players)

  if 'ata_round' in instance.dynamic_properties():
    raise ValueError("A game is already in progress.")

  for type in message_types:
    instance.delete_messages(type)

  # Lock membership by setting the max players to the current number
  # and removing public property
  instance.public = False
  instance.max_players = len(instance.players)

  instance.ata_nouns = list(noun_cards)
  instance.ata_characteristics = list(characteristic_cards)
  instance.ata_round = 1
  random.shuffle(instance.ata_nouns)
  random.shuffle(instance.ata_characteristics)

  # Pick a random player to be the leader
  instance.leader = random.choice(instance.players)

  put_list = []
  # Deal out the noun cards
  for player in instance.players:
    for i in xrange(hand_size):
      card = instance.ata_nouns.pop()
      message = models.Message(parent = instance, sender = instance.leader,
                               msg_type = 'ata_noun_card', recipient = player,
                               content = [card])
      put_list.append(message)

  put_list.extend(get_new_round_messages(instance))

  # Zero the scoreboard
  instance.scoreboard = '{}'

  instance.put()
  db.put(put_list)

  return [instance.leader]

def submit_card(instance, pid, arguments):
  if pid == instance.leader:
    raise ValueError("The leader may not submit a card.")

  if arguments[0] != instance.ata_round:
    message.put()
    raise ValueError("Current round is %d." % instance.ata_round)

  # Send the submitted cards to everyone
  message = models.Message(parent = instance, sender = pid,
                           msg_type = 'ata_player_submission', recipient = '',
                           content = [str(instance.ata_round), arguments[1], pid])
  message.put()
  instance.put()

  # Send the player a new card
  card = instance.ata_nouns.pop()
  return [card]

def end_turn(instance, pid, arguments):
  if pid != instance.leader:
    raise ValueError("Only the leader (%s) may end a turn." % instance.leader)

  if arguments[0] != instance.ata_round:
    message.put()
    raise ValueError("Current round is %d." % instance.ata_round)

  player = utils.check_playerid(arguments[1])
  card = arguments[2]
  if player not in instance.players:
    raise ValueError("%s is not in the Androids to Androids game." % player)

  instance.add_to_scoreboard(player, 1)

  # Check to see if anyone has won
  instance.leader = player
  if instance.get_score(player) == winning_score:
    return end_game(instance, card)

  # Start the new round
  instance.ata_round += 1
  db.put(get_new_round_messages(instance, card))
  instance.put()
  return card

def get_new_round_messages(instance, winning_card = None):
  put_list = []
  # Send a characteristic card to the leader
  new_card = instance.ata_characteristics.pop()
  content_list = [str(instance.ata_round), new_card]

  message = models.Message(parent = instance, sender = instance.leader,
                           msg_type = 'ata_char_card', recipient = instance.leader,
                           content = content_list)
  put_list.append(message)

  # Reveal the characteristic card to all of the other players
  if winning_card:
    content_list.append(winning_card)
  for player in instance.players:
    if player != instance.leader:
      message = models.Message(parent = instance, sender = instance.leader,
                               msg_type = 'ata_new_round', recipient = player,
                               content = content_list)
      put_list.append(message)
  return put_list

def end_game(instance, winning_card):
  for type in message_types:
    instance.delete_messages(type)

  content_list = [str(instance.ata_round), instance.leader,  winning_card]

  message = models.Message(parent = instance, sender = instance.leader,
                           msg_type = 'ata_game_over', recipient = '',
                           content = content_list)
  message.put()

  del instance.ata_nouns
  del instance.ata_characteristics
  del instance.ata_round
  instance.put()
  return instance.leader
