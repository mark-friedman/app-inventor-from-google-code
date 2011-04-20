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
Defines the request handlers for the game server. After retrieving
arguments from the request, all operations are run as database
transactions.  This means that any unhandled errors encountered
during the operations will result in the database performing a
'rollback' to the state that it was in before the request was made.

All server command functions return a tuple of the database model
they operated on and a dictionary of results. These vary from command
to command, but all requests will provide their return value using an
OperationResponse object.

The get functions for each request handler provide a simple web form
to perform the operation via a web interface and will write their
responses as a web page. Put functions write json to the request
handler that can be consumed by other applications.

Throughout this module, pid is accepted as an argument. The correct
format for a pid is of one of the following forms:
"Bill Magnuson" <billmag@mit.edu>
billmag@mit.edu

Received pids will be parsed for the email address and only the email
address will be used to identify players during game
operations. These same rules apply to other fields which identify
players such as a new leader or an invitee. In general, the variable
name 'player' will be used to represent values that are email
addresses and pid is used more generally to indicate that other
strings are acceptable as input.

For more information about the validation done on game ids, instance
ids, and player ids, look to utils.py.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

import sys
import logging
import traceback
import iso8601
import utils
from datetime import datetime
from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from models.game import Game
from models.game_instance import GameInstance
from models.message import Message
from server_commands import command_dict

####################
# Module Constants #
####################
# Operation Response Keys
REQUEST_TYPE_KEY = 'request_type'
ERROR_KEY = 'e'
RESPONSE_KEY = 'response'
GAME_ID_KEY = 'gid'
INSTANCE_ID_KEY = 'iid'
PLAYERS_KEY = 'players'
LEADER_KEY = 'leader'

# Request Parameter Keys
PLAYER_ID_KEY = 'pid'
INVITEE_KEY = 'inv'
TYPE_KEY = 'type'
CONTENTS_KEY = 'contents'
COMMAND_KEY = 'command'
ARGS_KEY = 'args'
MESSAGE_COUNT_KEY = 'count'
MESSAGE_RECIPIENTS_KEY = 'mrec'
MESSAGE_TIME_KEY = 'mtime'
INSTANCE_PUBLIC_KEY = 'makepublic'

####################
# Response Helpers #
####################

def run_with_response_as_transaction(req_handler, operation, *args, **kwargs):
  """ Run operation in a transaction and write its response to req_handler.

  Args:
    req_handler: The request handler to write a response to.
    operation: The callable function to run as a transaction.
    args: Positional arguments to pass to operation.
    kwargs: Keyword arguments to pass to operation.

  Runs operation as a database transaction, creates an
  OperationResponse with the return value and writes it to the
  request handler.

  If an exception raises to this function a traceback is written to
  the debug log and an OperationResponse is written to the request
  handler with the error message as its contents and the error key
  set to True.
  """
  try:
    response = db.run_in_transaction(operation, *args, **kwargs)
    OperationResponse(response = response).write_to_handler(req_handler)
  except BaseException, e:
    logging.debug('exception encountered: %s' % traceback.format_exc())
    OperationResponse(response = e.__str__(),
                       error = True).write_to_handler(req_handler)

class OperationResponse():
  """ Class for handling server operation responses and writing output.

  An OperationResponse is a standard way to provide a response to a
  server request. When operations are specific to a game instance,
  the operation response includes information about the current state
  of that instance.

  If an error is encountered during an operation the
  OperationResponse includes only the error boolean and the error's
  message as its response.

  Attributes:
    error: A boolean indicating that an error occurred during the
      execution of this operation.
    gid: The game id of the game for this operation.
    iid: The instance id of the game instance.
    leader: The current leader of the game instance.
    players: A list of players in the game instance
  """
  def __init__(self, response, error=False):
    """ Fill in parameters based on the error value and the model returned.

    Args:
      response: If no error occurs, response should be a tuple of the
        database model that this operation was performed with and a
        dictionary representing the response value of the operation.
        If an error is encountered, response should be an error
        message.
      error: A boolean indicating whether the operation encountered
        an error during execution.

    The OperationResponse's attributes are automatically filled in by
    reading the attributes of the model in the response tuple. If the
    model is a Game object then iid, leader and players are left with
    empty values.
    """
    self.error = error
    self.iid = ''
    self.leader = ''
    self.gid = ''
    self.players = []

    if self.error:
      self.response = response
    else:
      model, self.response = response
      if model and model.__class__.__name__ == 'GameInstance':
        self.gid = model.parent().key().name()
        self.iid = model.key().name()
        self.leader = model.leader
        self.players = model.players
      elif model and model.__class__.__name__ == 'Game':
        self.gid = model.key().name()

  def write_to_handler(self, req_handler):
    """ Writes a response to the req_handler.

    Args:
      req_handler: The request handler for this server request.

    If the 'fmt' field of this request is 'html' then the response is
    formatted to be written to the web. Otherwise, it is formatted to
    be sent as json.
    """
    if req_handler.request.get('fmt') == 'html':
      self.write_response_to_web(req_handler)
    else:
      self.write_response_to_phone(req_handler)

  def write_response_to_web(self, req_handler):
    """ Writes the response object to the request handler as html.

    Args:
      req_handler: The request handler for this server request.

    Writes a web page displaying the response object as it would
    be written to json.
    """
    req_handler.response.headers['Content-Type'] = 'text/html'
    req_handler.response.out.write('<html><body>')
    req_handler.response.out.write('''
        <em>The server will send this to the component:</em>
        <p />''')
    req_handler.response.out.write(
        self.get_response_object(req_handler.request.path))
    req_handler.response.out.write('''
    <p><a href="/">
    <i>Return to Game Server Main Page</i>
    </a>''')
    req_handler.response.out.write('</body></html>')

  def write_response_to_phone(self, req_handler):
    """ Writes the response object to the request handler as json.

    Args:
      req_handler: The request handler for this server request.
    """
    req_handler.response.headers['Content-Type'] = 'application/json'
    req_handler.response.out.write(
        self.get_response_object(req_handler.request.path))

  def get_response_object(self, request_type):
    """ Return a JSON object as a string with the fields of this response.

    Args:
      request_type: The type of server request that caused this
        operation.

    Creates a dictionary out of the fields of this object and encodes
    them in JSON.
    """
    response = simplejson.dumps({REQUEST_TYPE_KEY : request_type,
                                 ERROR_KEY : self.error,
                                 RESPONSE_KEY : self.response,
                                 GAME_ID_KEY : self.gid,
                                 INSTANCE_ID_KEY : self.iid,
                                 LEADER_KEY : self.leader,
                                 PLAYERS_KEY : self.players})
    logging.debug('response object: %s' % response)
    return response

#######################
# Operation Functions #
#######################

def get_instance_lists(gid, iid, pid):
  """ Return the instances that a player has been invited to and joined.

  Args:
    gid: The game id of the Game object that this method targets.
    iid: The instance id of the Game Instance object that this
      method targets.
    pid: A string containing the requesting player's email address.

  The gid and pid must be valid, but the iid can be blank. This is
  because a player must be able to query for lists of instances
  without being in one.

  Returns:
    A tuple containing a database model and a dictionary of instance
    lists.  The database model will be a Game Instance if the gid and
    iid parameters specify a valid GameInstance, otherwise the model
    will be a Game.  Instance lists are returned in the same format
    as get_instance_lists_dictionary.

  Raises:
    ValueError if the game id or player id are invalid.
  """
  utils.check_gameid(gid)
  player = utils.check_playerid(pid)
  model = game = utils.get_game_model(gid)
  if game is None:
    game = Game(key_name = gid, instance_count = 0)
    game.put()
    model = game
  elif iid:
    instance = utils.get_instance_model(gid,iid)
    if instance:
      model = instance
  instance_lists = get_instances_lists_as_dictionary(game, player)
  return model, instance_lists

def invite_player(gid, iid, invitee):
  """ Add invitee to the list of players invited to the specified instance.

  Args:
    gid: The game id of the Game object that this method targets.
    iid: The instance id of the Game Instance object that this
      method targets.
    invitee: The player id of the person to invite.

  Only modifies the instance if the player has not already been
  invited and has not joined the game.

  Returns:
    A tuple of the game instance and a single item dictionary:
      inv: The email address of the invited player if they are
        invited. If the player is not invited (because they have
        already been invited or have already joined the game), the
        value of 'inv' is the empty string.

  Raises:
    ValueError if the game id, iid or invitee email address are
    invalid.
  """
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  player = utils.check_playerid(invitee)
  instance = utils.get_instance_model(gid, iid)
  if player not in instance.invited and player not in instance.players:
    instance.invited.append(player)
    instance.put()
  else:
    player = ''
  return instance, {INVITEE_KEY : player}


def join_instance(gid, iid, pid):
  """ Attempt to add a player to an instance.

  Args:
    gid: The game id of the Game object that this method targets.
    iid: The instance id of the Game Instance to join.
    pid: A string containing the requesting player's email address.

  A player can join a game instance if it is not full and either the
  instance is public or the player has been invited. If this
  operation is invoked by a player that is not current in the
  specified instance and they are unable to join, it will fail.

  If the player is already in the game instance this will succeed
  without modifying the instance.

  If the specified game instance doesn't exist, it will be created as
  in new_instance with the specified instance id.

  If no players are in the game when this player tries to join they
  will automatically become the leader.

  Returns:
    A tuple of the game instance and the instance list dictionary
    for this player (see get_instance_lists_as_dictionary).

  Raises:
    ValueError if the game id, instance id or player id are invalid.
    ValueError if the player is not already in the game and is unable
      to join.
  """
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  player = utils.check_playerid(pid)
  instance = utils.get_instance_model(gid, iid)
  if instance is None:
    return new_instance(gid, iid, pid)
  game = instance.parent()
  instance_lists = get_instances_lists_as_dictionary(game, player)
  instance.add_player(player)
  instance.put()
  if iid in instance_lists['invited']:
    instance_lists['invited'].remove(instance.key().name())
  if iid not in instance_lists['joined']:
    instance_lists['joined'].append(instance.key().name())
  return instance, instance_lists

def leave_instance(gid, iid, pid):
  """ Remove a player from an instance.

  Args:
    gid: The game id of the game object that this method targets.
    iid: The instance id of the Game Instance to remove the player
      from.
    player: The player wishing to leave the instance.

  If the player that leaves the instance is the leader, the first
  player on the players lists becomes the leader.

  If no players are left, the maximum number of players allowed in
  this instance is set to -1 so that no one may join it in the
  future. This means that if someone tries to create an instance in
  the future with the same instance id, they will end up with one with
  a number appended to it (because this GameInstance object will still
  exist).

  The decision to do this was made because it is not yet possible to
  reliably delete all of the messages in a game instance (see
  models/game_instance.py). Thus, if players are able to join an
  orphaned instances, the old messages could still be available. If,
  in the future, App Engine adds ways to reliably delete database
  models this behavior could be changed to delete the instance
  entirely if everyone leaves.

  Returns:
    A tuple of the game object and the instance list dictionary
    for this player (see get_instance_lists_as_dictionary).

  Raises:
    ValueError if the player is not currently in the instance.
  """
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  instance = utils.get_instance_model(gid, iid)
  player = instance.check_player(pid)
  instance.players.remove(player)
  if player == instance.leader and len(instance.players) != 0:
    instance.leader = instance.players[0]
  if len(instance.players) == 0:
    instance.max_players = -1
  game = instance.parent()
  instance_lists = get_instances_lists_as_dictionary(game, player)
  instance_lists['joined'].remove(instance.key().name())
  instance.put()
  return game, instance_lists

def get_messages(gid, iid, message_type, recipient, count, time):
  """ Retrieve messages matching the specified parameters.

  Args:
    gid: The game id of the Game object that is a parent of the
      desired instance.
    iid: This instance id of the Game Instance to fetch messages
      from.
    message_type: A string 'key' for the message. If message_type is
      the empty string, all message types will be returned.
    recipient: The player id of the recipient of the messages. This
      operation will also return messages that are sent with an empty
      recipient field.
    count: The maximum number of messages to retrieve.
    time: A string representation of the earliest creation time of a
      message to returned. Must be in ISO 8601 format to parse
      correctly.

  Uses the get_messages function of the GameInstance class to
  retrieve messages.

  Returns:
    A tuple of the game instance and a dictionary with two items:
      'count': The number of messages returned.
      'messages': A list of the dictionary representations of the
        fetched messages.
  """
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  instance = utils.get_instance_model(gid, iid)
  recipient = instance.check_player(recipient)
  messages = instance.get_messages(count=count,
                                   message_type=message_type,
                                   recipient=recipient, time=time)
  return instance, {MESSAGE_COUNT_KEY : len(messages),
                    'messages' : messages}

def new_instance(gid, iid_prefix, pid, make_public = False):
  """ Create a new instance of the specified game.

  Args:
    gid: The game id of the Game parent of the new instance.
    iid_prefix: The desired instance id. If no instance has been made
      with this name before, then this will be the instance id of the
      newly created instance. However, since instance ids must be
      unique, the actual instance id will likely be iid_prefix with a
      number suffix.
    pid: The id of the first player and leader of the game.
    make_public: A boolean indicating whether this instance should
      be able to be seen and joined by anyone.

  The instance id will start with iid_prefix, but could have any
  suffix. If the parent Game object does not exist, it will
  automatically be created.

  Returns:
    A tuple of the newly created instance and an instance lists
    dictionary (see get_instance_lists_as_dictionary).

  Raises:
    ValueError if the gameid or player id are invalid.
  """
  utils.check_gameid(gid)
  player = utils.check_playerid(pid)
  game = Game.get_by_key_name(gid)
  if game is None:
    game = Game(key_name = gid, instance_count = 0)

  if not iid_prefix:
    iid_prefix = player + 'instance'
  instance = game.get_new_instance(iid_prefix, player)

  instance_lists = get_instances_lists_as_dictionary(game, player)
  instance_lists['joined'].append(instance.key().name())
  if make_public:
    instance.public = True
    instance_lists['public'].append(instance.key().name())
  instance.put()
  game.put()

  return instance, instance_lists

def new_message(gid, iid, pid, message_type, message_recipients,
                message_content):
  """ Create new messages and put them in the database.

  Args:
    gid: The game id of the Game parent of the instance to create a
      message for.
    iid: The instance id of the GameInstance to create a message for.
    pid: The player id of the message sender.
    message_type: A string that acts as a key for the message.
    message_recipients: The recipients of the message formatted in
      JSON. This can be a single player id as a JSON string, a list
      of player ids in a JSON array or the empty string. Messages
      sent with the empty string as a recipient can be fetched by
      any player.
    message_content: The string representation of a JSON value to be
      sent as the content of the message.

  Returns:
    A tuple of the specified game instance and a dictionary with
    two items:
      'count' : The number of messages created.
      'mrec' : The list of email addresses that were sent messages.

  Raises:
    ValueError if the requesting player or any of the message
      recipients are not members of the specified game instance.
  """
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  instance = utils.get_instance_model(gid, iid)
  player = instance.check_player(pid)
  recipients_list = None
  if message_recipients != '':
    recipients_list = simplejson.loads(message_recipients)
    if isinstance(recipients_list, basestring):
      recipients_list = [recipients_list]
  if not recipients_list:
    recipients_list = ['']
  message_list = []
  for recipient_entry in recipients_list:
    if recipient_entry:
      recipient_entry = instance.check_player(recipient_entry)
    message = Message(parent = instance,
                      sender = player,
                      msg_type = message_type,
                      recipient = recipient_entry,
                      content = message_content)
    message_list.append(message)
  db.put(message_list)
  return instance, {MESSAGE_COUNT_KEY : len(message_list),
                    MESSAGE_RECIPIENTS_KEY : recipients_list}

def server_command(gid, iid, pid, command, arguments):
  """ Performs the desired server command.

  Args:
    gid: The game id of the Game model for this operation.
    iid: The instance id of the GameInstance model for
      this operation.
    pid: The player id of the requesting player.
    command: The key identifying the command to execute.
    arguments: JSON representation of arguments to the command.

  If the gid and iid specify a valid game instance model it will be
  passed to the server command. In the case that the iid is empty or
  refers to a game instance that doesn't exist, a game model will be
  used. Most commands will fail if passed a game model instead of a
  game instance, but some are indifferent to the model passed to
  them.

  Unless the dynamic property do_not_put has been set to False, this
  will put the database model after the command has been
  performed. This means that server commands do not need to make
  intermediate puts of the instance model passed to them.

  Returns:
    A tuple of the model used in the server command's execution and a
    two item dictionary:
      'type': The requested command key.
      'contents': A Python value of the response value of the
        command. This varies among server commands but must always be
        able to be encoded to JSON.

  Raises:
    ValueError if the game id or player id is invalid.
    ValueError if the arguments json cannot be parsed.
    ValueError if command is not a known server command.
  """
  utils.check_gameid(gid)
  player = utils.check_playerid(pid)
  model = None
  if iid:
    model = utils.get_instance_model(gid, iid)
  if model is None:
    model = utils.get_game_model(gid)
    if model is None:
      model = Game(key_name = gid, instance_count = 0)

  arguments = simplejson.loads(arguments)
  reply = ''

  if command in command_dict:
    reply = command_dict[command](model, player, arguments)
    if 'do_not_put' not in model.dynamic_properties() or not model.do_not_put:
      model.put()
  else:
    raise ValueError("Invalid server command: %s." % command)

  if not isinstance(reply, list):
    reply = [reply]
  return model, {TYPE_KEY : command, CONTENTS_KEY: reply}

def set_leader(gid, iid, pid, leader):
  """ Set the leader of the specified instance.

  Args:
    gid: The game id of the GameInstance object's parent Game object.
    iid: The instance id of the GameInstance to change the leader of.
    pid: The player id of the requesting player. This player must be
      the current instance leader in oder to change the leader value.
    leader: The player id of the new leader.

  Returns:
    A tuple of the change game instance model and a dictionary with
    two items:
      'current_leader' : The leader after attempting this change.
      'leader_change' : Whether or not this attempt to set the leader
        succeeded.
  Raises:
    ValueError if the game id or instance id are invalid.
    ValueError if player or leader are in the specified game
      instance.
  """
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  instance = utils.get_instance_model(gid, iid)
  player = instance.check_player(pid)
  leader = instance.check_player(leader)
  if player != instance.leader or instance.leader == leader:
    return instance, {'current_leader' : instance.leader,
                      'leader_changed' : False}
  instance.leader = leader
  instance.put()
  return instance, {'current_leader' : leader,
                    'leader_changed' : True}

def get_instance(gid, iid):
  """ Retrieves an instance and its dictionary.

  Args:
    gid: The game id of the desired GameInstance object's parent Game
      object.
    iid: The instance id of the desired GameInstance object.

  Returns:
    A tuple of the game instance object and its dictionary
    representation.

  Raises:
    ValueError if the game id or instance id are not valid.
  """
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  instance = utils.get_instance_model(gid, iid)
  return instance, instance.to_dictionary()

##################
# Writer Helpers #
##################

def get_instances_lists_as_dictionary(game, player):
  """ Return a dictionary with joined and invited instance id lists for player.

  Args:
    game: The Game database model that is the parent of the instances
      to query.
    player: The email address of the player to get instance lists for.

  Returns:
    A dictionary of lists:
      'joined' : The list of instance ids of all all instances that
        the player has joined and not subsequently left.
      'invited' : The list of instance ids of all instances that the
        player has been invited to and not yet joined.
  """
  return {'joined' : get_instances_joined(game, player),
          'invited' : get_instances_invited(game, player),
          'public' : get_public_instances(game)}

def get_instances_joined(game, player):
  """ Return the instance ids of instance that player has joined.

  Args:
    game: The parent Game database model to query for instances.
    player: The email address of the player to look for in instances.

  Returns:
    An empty list if game is None. Else, returns a list of the instance
    ids of all instances with game as their parent that have player in
    their joined list.
  """
  if game is None:
    return []
  query = game.get_joined_instance_keys_query(player)
  return [key.name() for key in query]

def get_instances_invited(game, player):
  """ Return the instance ids of instances that player has been invited to.

  Args:
    game: The parent Game database model to query for instances.
    player: The email address of the player to look for in instances.

  Returns:
    An empty list if game is None. Else, returns a list of the
    instance ids of all instances with game as their parent that have
    player in their invited list.
  """
  if game is None:
    return []
  query = game.get_invited_instance_keys_query(player)
  return [key.name() for key in query]

def get_public_instances(game):
  """ Return the instance ids of public instances for the specified game.

  Args:
    game: The parent Game database model to query for instances.

  Returns:
    An empty list if game is None. Else, returns a list of the
    instance ids of all joinable public instances with game as
    their parent.
  """
  if game is None:
    return []
  query = game.get_public_instances_query(keys_only = True)
  return [key.name() for key in query]

###########################
# Request Handler Classes #
###########################

class MainPage(webapp.RequestHandler):
  """ The request handler for the index page of the game server. """
  def get(self):
    """Write a simple web page for displaying server information. """
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write('<html><body>')
    self.response.out.write('<h1>Game Server for App Inventor Game'
        ' Client Component</h1>')
    self.write_game_list()
    self.write_methods()
    self.response.out.write('''
    <p><a href="http://appengine.google.com">
    <small><i>Go to AppEngine Administration Console</i></small>
    </a>''')
    self.response.out.write('</body></html>')

  def write_game_list(self):
    """ Create an HTML table showing game instance information. """
    self.response.out.write('''
    <p><table border=1>
      <tr>
         <th>Created
         <th>Game</th>
         <th>Instance</th>
         <th>Players</th>
         <th>Invitees</th>
         <th>Leader</th>
         <th>Public</th>
         <th>Max Players</th>
         <th colspan="2">More ...</th>
      </tr>''')
    games = db.GqlQuery("SELECT * FROM GameInstance")
    for game in games:
      self.response.out.write(
          '<tr><td>%s UTC</td>\n' % game.date.ctime())
      self.response.out.write('<td>%s</td>' % game.parent().key().name())
      self.response.out.write('<td>%s</td>' % game.key().name())
      self.response.out.write('<td>')
      for player in game.players:
        self.response.out.write(' %s' % player)
      self.response.out.write('</td>\n')
      self.response.out.write('<td>')
      for invite in game.invited:
        self.response.out.write(' %s' % invite)
      self.response.out.write('</td>\n')
      self.response.out.write('<td>')
      self.response.out.write(' %s' % game.leader)
      self.response.out.write('</td>\n')
      self.response.out.write('<td>')
      self.response.out.write(' %s' % game.public)
      self.response.out.write('</td>\n')
      self.response.out.write('<td>')
      self.response.out.write(' %s' % game.max_players)
      self.response.out.write('</td>\n')
      self.response.out.write('''
      <td><form action="/getinstance" method="post"
            enctype=application/x-www-form-urlencoded>
            <input type="hidden" name="gid" value="%s">
            <input type="hidden" name="iid" value="%s">
            <input type="hidden" name="fmt" value="html">
            <input type="submit" value="Game state"></form></td>\n''' %
                              (game.parent().key().name(), game.key().name()))
      self.response.out.write('</tr>')
    self.response.out.write('</table>')

  def write_methods(self):
    """ Write links to the available server request pages. """
    self.response.out.write('''
        <p />Available calls:\n
        <ul>
        <li><a href="/newinstance">/newinstance</a></li>
        <li><a href="/invite">/invite</a></li>
        <li><a href="/joininstance">/joininstance</a></li>
        <li><a href="/leaveinstance">/leaveinstance</a></li>
        <li><a href="/newmessage">/newmessage</a></li>
        <li><a href="/messages">/messages</a></li>
        <li><a href="/setleader">/setleader</a></li>
        <li><a href="/getinstance">/getinstance</a></li>
        <li><a href="/getinstancelists">/getinstancelists</a></li>
        <li><a href="/servercommand">/servercommand</a></li>
        </ul>''')

class GetInstanceLists(webapp.RequestHandler):
  """ Request handler for the get_instance_lists operation. """
  def post(self):
    """ Execute get_instance_lists and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game to get instances of.
      iid: The instance id of the game instance to execute the
        command with. This is optional for this command, although,
        including it will result in the ResponseObject including
        leader and player information.
      pid: The player id of the requesting player.
    """
    logging.debug('/getinstancelists?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    pid = self.request.get(PLAYER_ID_KEY)
    run_with_response_as_transaction(self, get_instance_lists, gid, iid, pid)

  def get(self):
    """ Write a short HTML form to perform a get_instance_lists operation."""
    self.response.out.write('''
    <html><body>
    <form action="/getinstancelists" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Get Instance Lists">
    </form>''')
    self.response.out.write('</body></html>\n')

class GetMessages(webapp.RequestHandler):
  """ Request handler for the get_messages operation. """
  def post(self):
    """ Execute get_messages and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game.
      iid: The instance id of the game instance to execute the
        command with.
      pid: The player id of the message recipient.
      type: The type of messages requested or the empty string to
        retrieve all messages.
      count: An integer number of messages to retrieve. This is
        treated as a maximum and defaults to 1000 if there is a
        failure retrieving the count parameter.
      mtime: A string in ISO 8601 date format. All messages returned
        will have a creation time later than this time. Defaults to
        datetime.min if there is a failure in retrieving or parsing
        the parameter.
    """
    logging.debug('/messages?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    message_type = self.request.get(TYPE_KEY)
    recipient = self.request.get(PLAYER_ID_KEY)

    count = 1000
    try:
      count = int(self.request.get(MESSAGE_COUNT_KEY))
    except ValueError:
      pass

    time = datetime.min
    try:
      time_string = self.request.get(MESSAGE_TIME_KEY)
      if time_string is not None and time_string != '':
        time = iso8601.parse_date(time_string)
    except ValueError:
      pass

    run_with_response_as_transaction(self, get_messages, gid, iid,
                                     message_type, recipient, count, time)

  def get(self):
    """ Write a short HTML form to perform a get_messages operation."""
    self.response.out.write('''
    <html><body>
    <form action="/messages" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Message type <input type="text" name="type" /> </p>
       <p>Email <input type="text" name="pid" /> </p>
       <p>Count <input type="text" name="count" /> </p>
       <p>Time <input type="text" name="mtime" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Get Messages">
    </form></body></html>\n''')

class InvitePlayer(webapp.RequestHandler):
  """ Request handler for the invite_player operation."""
  def post(self):
    """ Execute invite_player and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game.
      iid: The instance id of the game instance to invite the
        player to.
      pid: The player id of the requesting player.
      inv: The player id of the player to invite.
    """
    logging.debug('/invite?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    inv = self.request.get(INVITEE_KEY)
    run_with_response_as_transaction(self, invite_player, gid, iid, inv)

  def get(self):
    """ Write a short HTML form to perform an invite_player operation."""
    self.response.out.write('''
    <html><body>
    <form action="/invite" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /></p>
       <p>Invitee <input type="text" name="inv" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Invite player">
    </form>''')
    self.response.out.write('</body></html>\n')

class JoinInstance(webapp.RequestHandler):
  """ Request handler for the join_instance operation."""
  def post(self):
    """ Execute join_instance and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game.
      iid: The instance id of the game instance to join.
      pid: The player id of the requesting player.
    """
    logging.debug('/joininstance?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    pid = self.request.get(PLAYER_ID_KEY)
    run_with_response_as_transaction(self, join_instance, gid, iid, pid)

  def get(self):
    """ Write a short HTML form to perform a join_instance operation."""
    self.response.out.write('''
    <html><body>
    <form action="/joininstance" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Join Instance">
    </form>''')
    self.response.out.write('</body></html>\n')

class LeaveInstance(webapp.RequestHandler):
  """ Request handler for the leave_instance operation."""
  def post(self):
    """ Execute leave_instance and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game.
      iid: The instance id of the game instance to leave.
      pid: The player id of the requesting player.
    """
    logging.debug('/leaveinstance?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    pid = self.request.get(PLAYER_ID_KEY)
    run_with_response_as_transaction(self, leave_instance, gid, iid, pid)

  def get(self):
    """ Write a short HTML form to perform a leave_instance operation."""
    self.response.out.write('''
    <html><body>
    <form action="/leaveinstance" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Leave Instance">
    </form>''')
    self.response.out.write('</body></html>\n')


class NewInstance(webapp.RequestHandler):
  """ Request handler for the new_instance operation."""
  def post(self):
    """ Execute new_instance and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game.
      iid: The proposed instance id of the new instance. The instance
        id of the created instance could differ from this if the
        proposed id is already in use.
      pid: The player id of the requesting player.
      make_public: A boolean indicating whether this instance should
        be able to be seen and joined by anyone.
    """
    logging.debug('/newinstance?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    pid = self.request.get(PLAYER_ID_KEY)
    make_public = False
    try:
      make_public = utils.get_boolean(self.request.get(INSTANCE_PUBLIC_KEY))
    except ValueError:
      pass
    run_with_response_as_transaction(self, new_instance, gid, iid,
      pid, make_public)

  def get(self):
    """ Write a short HTML form to perform a new_instance operation."""
    self.response.out.write('''
    <html><body>
    <form action="/newinstance" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>First player ID <input type="text" name="pid" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="New Instance">
    </form></body></html>\n''')

class NewMessage(webapp.RequestHandler):
  """ Request handler for the new_message operation. """
  def post(self):
    """ Execute new_message and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game.
      iid: The instance id of the game instance add messages to.
      pid: The player id of the requesting player.
      type: The message type key.
      mrec: Json representation of the recipients of the message.
      content: Json representation of the contents of the message.
    """
    logging.debug('/newmessage?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    pid = self.request.get(PLAYER_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    message_type = self.request.get(TYPE_KEY)
    message_recipients = self.request.get(MESSAGE_RECIPIENTS_KEY)
    message_content = self.request.get(CONTENTS_KEY)
    run_with_response_as_transaction(self, new_message, gid, iid, pid,
                                     message_type, message_recipients,
                                     message_content)

  def get(self):
    """ Write a short HTML form to perform a new_message operation."""
    self.response.out.write('''
    <html><body>
    <form action="/newmessage" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /></p>
       <p>Message type <input type="text" name="type" /> </p>
       <p>Message Recipients (Json array) <input type="text" name="mrec" />
       </p>
       <p>Message Contents (Json array) <input type="text" name="contents" />
       </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Send Message">
    </form>''')
    self.response.out.write('''<p> Expected format for recipients: <br>
                            ["email@domain.com", "email2@domain.com"] </p>''')
    self.response.out.write('''<p> Expected format for contents: <br>
                            ["string 1", "string 2"] </p>''')
    self.response.out.write('''</body></html>\n''')


class ServerCommand(webapp.RequestHandler):
  """ Request handler for the server_command operation. """
  def post(self):
    """ Execute server_command and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game to execute the command
        with.
      iid: The instance id of the game instance to execute the
        command with.
      pid: The player id of the requesting player.
      command: The key of the command.
      arguments: Json representation of the arguments to the
        server command.
    """
    logging.debug('/servercommand?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    pid = self.request.get(PLAYER_ID_KEY)
    command = self.request.get(COMMAND_KEY)
    arguments = self.request.get(ARGS_KEY)
    run_with_response_as_transaction(self, server_command, gid, iid, pid,
                                     command, arguments)

  def get(self):
    """ Write a short HTML form to perform a set_leader operation."""
    self.response.out.write('''
    <html><body>
    <form action="/servercommand" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /> </p>
       <p>Command <input type="text" name="command" /> </p>
       <p>Arguments (Json array) <input type="text" name="args" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Send Command">
    </form>''')
    self.response.out.write('''</body></html>\n''')

class SetLeader(webapp.RequestHandler):
  """ Request handler for the set_leader operation.  """
  def post(self):
    """ Execute set_leader and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game.
      iid: The instance id of the game instance to change the
        leader of.
      leader: The player id of the new leader candidate.
      pid: The player id of the requesting player.
    """
    logging.debug('/setleader?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    leader = self.request.get(LEADER_KEY)
    pid = self.request.get(PLAYER_ID_KEY)

    run_with_response_as_transaction(self, set_leader, gid, iid, pid, leader)

  def get(self):
    """ Write a short HTML form to perform a set_leader operation."""
    self.response.out.write('''
    <html><body>
    <form action="/setleader" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /></p>
       <p>New leader (player id) <input type="text" name="leader" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Set leader">
    </form>''')
    self.response.out.write('</body></html>\n')

#############################################
# Handlers not used by GameClient component #
#############################################

class GetInstance(webapp.RequestHandler):
  """ Request handler for the get_instance operation."""
  def post(self):
    """ Execute get_instance and write the response to the handler.

    Request parameters:
      gid: The game id of the parent Game.
      iid: The instance id of the game instance to get the
        information of.
    """
    logging.debug('/getinstance?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get(GAME_ID_KEY)
    iid = self.request.get(INSTANCE_ID_KEY)
    run_with_response_as_transaction(self, get_instance, gid, iid)

  def get(self):
    """ Write a short HTML form to perform a get_instance operation."""
    self.response.out.write('''
    <html><body>
    <form action="/getinstance" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Get Instance Info">
    </form>''')
    self.response.out.write('</body></html>\n')

##########################
# Application definition #
##########################

def application(custom_command_dict):
  """ Return the WSGI Application with the game server request handlers.

  Args:
    custom_command_dict: A dictionary of command name strings
      to functions.

  The custom_command_dict will be added to the server's command
  dictionary so that custom commands can be invoked with the
  ServerCommand request handler. If command names in
  custom_command_dict are the same as built in server commands they
  will overwrite the built in functions.
  """
  for command in custom_command_dict.iteritems():
    command_dict[command[0]] = command[1]
  return webapp.WSGIApplication([('/', MainPage),
                                 ('/newinstance', NewInstance),
                                 ('/invite', InvitePlayer),
                                 ('/joininstance', JoinInstance),
                                 ('/leaveinstance', LeaveInstance),
                                 ('/newmessage', NewMessage),
                                 ('/getinstancelists', GetInstanceLists),
                                 ('/messages', GetMessages),
                                 ('/setleader', SetLeader),
                                 ('/servercommand', ServerCommand),
                                 ('/getinstance', GetInstance)],
                                debug=True)
