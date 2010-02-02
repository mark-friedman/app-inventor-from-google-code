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
Contains the server commands dictionary as well as the implementation
of a number of server commands related to instance management. More
specific server commands are in the extensions folder.

To enable server commands, they must be entered into
commands_dict. Every server command should take in a database model
(either a game instance or a game), the email address of the player
that requested the server command and a list of arguments. The format
of the arguments and what is done with the player and the database
model depends on the command.

Server commands should be generally useful to creators of games and
not be created for a specific game. Additionally, command functions
should, where appropriate, only parse the arguments and perform their
actual operations in separate methods. This allows for custom modules
to utilize extensions more easily when creating game specific
functions.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

import logging
import traceback
import utils
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.runtime import apiproxy_errors
from django.utils import simplejson
from extensions import scoreboard
from extensions import card_game

EMAIL_SENDER = ""

def send_email_command(model, player, arguments):
  """ Send an email using App Engine's email server.

  Args:
    instance: Not used, can be any value.
    player: The player requesting that the email be sent.
    arguments: A two item list with the subject of the email as the
      first item and the body of the email as the second.

  EMAIL_SENDER must be defined above and be a listed developer
  of your AppEngine application for this to work successfully.

  Returns:
    True if the email sends succesfully, False otherwise.
  """
  if email_sender:
    message_recipient = arguments[0]
    message_content = arguments[1]
    mail.send_mail(sender=EMAIL_SENDER,
                   to=message_recipient,
                   subject=message_content[0],
                   body=message_content[1] +
                   '\nMessage sent from AppInventorGameServer by ' +
                   player + '.')
    return True
  return False

def set_public_command(instance, player, arguments):
  """ Set the public membership field for an instance.

  Args:
    instance: The GameInstance database model to change.
    player: The player requesting the change. This player must
      be the current leader of the instance.
    arguments: A single item list containing the desired
      boolean value for the public field of instance.

  A public game can be joined by players without first being
  invited. Changing the value of public does not change the current
  membership of the game.

  Returns:
    The new value of public for the instance.

  Raises:
    ValueError if the requesting player is not the leader of the
      instance.
    ValueError if the argument is unable to be parsed into a boolean.
  """
  instance.check_leader(player)
  value = utils.get_boolean(arguments[0])
  instance.public = value
  return value

def set_max_players_command(instance, player, arguments):
  """ Set the maximum number of players allowed to join an instance.

  Args:
    instance: The GameInstance database model to change.
    player: The player requesting the change. This player must be the
      current leader of the instance.
    arguments: A single item list containing the desired integer value
      for the max players of this instance.

  If the maximum player count is set to a value lower than the current
  number of players, no players will be removed. However, new players
  will not be able to join until the max players count goes up or
  enough players leave the instance that the number of players is less
  than the maximum.

  Returns:
    The new value of max_players for the instance.

  Raises:
    ValueError if the requesting player is not the leader of the
      instance.
    ValueError if the argument is unable to be parsed into an integer.
  """
  instance.check_leader(player)
  max_players = int(arguments[0])
  instance.max_players = max_players
  return max_players

def get_public_instances_command(model, player, arguments = None):
  """ Return a list of public instances of the specified game.

  Args:
    model: Either a Game or GameInstance database model. If model is a
      GameInstance, this will return the public instances of its
      parent Game.
    player: Not used. Value can be anything.
    arguments: Not used, can be any value.

  Returns:
    A list of all public instances in this game that have less players
    than their maximum (i.e. can be joined). Instances are sorted with
    the newest ones first. Each entry in the list of instances is
    itself a three item list with the instance id as the first item,
    the number of players currently in the game as the second item and
    the maximum number of players (if any) as the third item. If no
    maximum number of players is set for the game instance the third
    item will be set to zero.
  """
  game = utils.get_game(model)
  public_instances = game.get_public_instances_query().fetch(1000)
  return [[i.key().name(), len(i.players), i.max_players]
          for i in public_instances]

def delete_instance_command(instance, player, arguments = None):
  """ Delete an instance and its messages.

  Args:
    instance: The instance to delete.
    player: The player requesting the deletion. This player must
      be the current leader of the instance.
    arguments: Not used, can be any value.

  Makes a good faith effort to delete the messages, but deleting large
  numbers of database entries is currently very buggy in
  AppEngine. This will hopefully get better over time as AppEngine
  advances. See the method delete_messages in models/game_instance.py
  for more information.

  If the deletion of messages fails the exception will be logged and
  this command will return normally.

  Returns:
    True if the instance deletes succesfully.

  Raises:
    ValueError if player is not the leader of the instance.
    ValueError if instance is not a GameInstance model.
  """
  if instance.__class__.__name__ != 'GameInstance':
    raise ValueError("Only models of type GameInstance may be deleted.")

  instance.check_leader(player)
  try:
    instance.delete_messages()
  except apiproxy_errors.ApplicationError, err:
    logging.debug("Exception during message deletion: %s" %
                  traceback.format_exc())
  db.delete(instance)
  instance.do_not_put = True
  return True

def decline_invite_command(instance, player, arguments = None):
  """ Remove a player from the invited list of an instance.

  Args:
    instance: The instance to uninvite player from.
    player: The player wishing to decline an invite.
    arguments: Not used, can be any value.

  If the player wasn't actually invited to the game, nothing happens
  and this method returns false.

  Returns:
    True if the player was previously invited to the game, False
    otherwise.
  """
  if player in instance.invited:
    instance.invited.remove(player)
    return True
  return False

command_dict = {
  'sys_email' : send_email_command,
  'sys_set_public' : set_public_command,
  'sys_set_max_players' : set_max_players_command,
  'sys_get_public_instances' : get_public_instances_command,
  'sys_delete_instance' : delete_instance_command,
  'sys_decline_invite' : decline_invite_command,

  # Scoreboard commands.
  'scb_get_scoreboard' : scoreboard.get_scoreboard_command,
  'scb_get_score' : scoreboard.get_score_command,
  'scb_add_to_score' : scoreboard.add_to_score_command,
  'scb_set_score' : scoreboard.set_score_command,
  'scb_clear_scoreboard' : scoreboard.clear_scoreboard_command,

  # Card commands.
  'crd_set_deck' : card_game.set_deck_command,
  'crd_deal_cards' : card_game.deal_cards_command,
  'crd_draw_cards' : card_game.draw_cards_command,
  'crd_discard' : card_game.discard_command,
  'crd_pass_cards' : card_game.pass_cards_to_player_command,
  'crd_cards_left' : card_game.get_cards_remaining_command
  }
