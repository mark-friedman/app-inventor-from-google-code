# Copyright 2009 Google Inc.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#      http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" The GameInstance database model class and associated methods."""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from datetime import datetime
from django.utils import simplejson
from game_server import utils
from google.appengine.ext import db
from message import Message

class GameInstance(db.Expando):
  """ A model for an instance of a game.

  A GameInstance contains all of the membership and message
  information for an instance of a particular game. It is implemented
  as an Expando model to allow extensions and custom modules to add
  dynamic properties in order to extend the functionality of the
  instance.

  The key_name of a GameInstance should be the unique instance id.  A
  GameInstance's parent is the Game model that it is an instance of.

  Attributes:
    players: A list of the email addresses of players currently in the
      instance.
    invited: A list of email addresses of invited players.
    leader: The player that is currently the leader of the instance.
    date: The date of creation, automatically set upon instantiation.
    public: A bool that determines whether a player must first be
      invited before they can join this instance.
    full: A boolean indicating whether or not the game has reached
      its maximum membership. Automatically set when the GameInstance
      is put.
    max_players: An integer for the maximum number of players allowed
      in this instance or 0 if there is no maximum.

  """
  players = db.StringListProperty(required=True)
  invited = db.StringListProperty(default=[])
  leader = db.StringProperty(required=True)
  date = db.DateTimeProperty(required=True, auto_now=True)
  public = db.BooleanProperty(default=False)
  full = db.BooleanProperty(default=False)
  max_players = db.IntegerProperty(default=0)

  def put(self):
    """ Set the value of full and put this instance in the database. """
    self.set_full()
    db.Model.put(self)

  def set_full(self):
    """ Set the full attribute of this entity appropriately.

    This should be called at put time to make sure that any stored
    GameInstance model has the appropriate value for full. A game is
    full if it has a non-zero value for max players which is less than
    or equal to the number of players in the game.
    """
    if self.max_players == 0 or self.max_players > len(self.players):
      self.full = False
    else:
      self.full = True

  def to_dictionary(self):
    """ Return a dictionary representation of the instance's attributes. """
    return {'gameid' : self.parent().key().name(),
            'instanceId' : self.key().name(),
            'leader' : self.leader,
            'players' : self.players,
            'invited' : self.invited,
            'public' : self.public,
            'max_players' : self.max_players}

  def __str__(self):
    """ Return a json string of this model's dictionary. """
    return simplejson.dumps(self.to_dictionary())

  def create_message(self, sender, msg_type, recipient, content):
    """ Create a new message model with this instance as its parent.

    Args:
      sender: A string describing the creator of the message.
      msg_type: A string that acts as a key for the message.
      recipient: The intended recipient of this message. The
        recipient should either be the empty string or an email
        address. Messages sent with the empty string as their
        recipient can be fetched by any player.
      content: A python list or dictionary representing the content
        of this message. Converted to a json string for storage.

    Returns:
      A new Message model with the specified attributes. This model
      has not yet been put in the database.
    """
    return Message(parent = self, sender = sender, msg_type = msg_type,
                   recipient = recipient, content = simplejson.dumps(content))

  def get_messages(self, time = datetime.min, count = 1000,
                   message_type='', recipient=''):
    """ Return a list of message dictionaries using query_messages.

    Args (optional):
      time: (default: datetime.min) All messages retrieved must have
        been created after this time..
      count: (default 1000) The maximum number of messages to
        retrieve.
      message_type: (default '') The message type to retrieve. If
        left as None or the empty string then all messages matching
        other criteria will be returned.
      recipient: (default '') The recipient of the messages to
        retrieve.  All messages sent with a recipient of the empty
        string will also be retrieved.

    Returns:
      The dictionary representation of all messages matching the
      above criteria that were created with this instance as the
      parent. The newest 'count' messages (that are newer than time)
      are retrieved and then returned in order such that the first
      message in the returned list is the oldest.

      Note that the first message returned is not necessarily the
      oldest one that is newer than time. This can occur if the
      number of matching messages is greater than 'count' since the
      'count' newest are selected before their order is reversed.
    """
    return [message.to_dictionary() for message in
            self.get_messages_query(message_type, recipient,
                                    time = time).fetch(count)[::-1]]

  def get_messages_query(self, message_type, recipient,
                         time = datetime.min, sender = None,
                         keys_only = False):
    """ Return a message query from this instance.

    Args:
      message_type: The message type to retrieve. If left as None or
        the empty string then all messages matching other criteria
        will be returned.
      recipient: The recipient of the messages to retrieve. All
        messages sent with a recipient of the empty string will also
        be retrieved.
      time: All messages retrieved must have been created after this
        time.
      sender: The sender of the message.
      keys_only: If keys_only is set to true, this will only search
        for messages that have recipient = recipient. Thus, it will
        only include messages sent with no recipient if recipient
        is set to ''.

    Returns:
      A query object that can be fetched or further modified.
    """
    query = Message.all(keys_only = keys_only)
    query.ancestor(self.key())
    query.filter('date >', time)
    if message_type is not None and message_type != '':
      query.filter('msg_type =', message_type)
    if sender:
      query.filter('sender =', sender)
    # Avoid doing two queries when we don't need to.
    if recipient == '':
      query.filter('recipient =', '')
    else:
      if keys_only:
        query.filter('recipient =', recipient)
      else:
        query.filter("recipient IN", [recipient, ''])
    query.order('-date')
    return query

  def delete_messages(self, mtype = None):
    """ Delete messages of a specified kind.

    Args:
      type: A string of the message type to delete.

    Due to timeout issues with App Engine, this method will currently
    only succeed when running on App Engine if the number of messages
    being deleted is relatively small (~hundreds). It will attempt to
    delete up to 1000. The timeout retry wrapper (see
    game_server/autoretry_datastore.py) and using keys only search
    drastically increases the chances of success, but this method is
    still not guaranteed to complete.

    For more information see:
    http://groups.google.com/group/google-appengine/
      browse_thread/thread/ec0800a3ca92fe69?pli=1
    http://stackoverflow.com/questions/108822/
      delete-all-data-for-a-kind-in-google-app-engine
    """
    if mtype:
      db.delete(Message.all(keys_only = True).filter('msg_type =', mtype)
                .ancestor(self.key()).order('date').fetch(1000))
    db.delete(Message.all(keys_only = True).ancestor(self.key()).order('date')
              .fetch(1000))

  def check_player(self, pid):
    """ Confirm that a player is currently in the instance.

    Args:
      pid: A string containing the player's email address.

    Returns:
      The email address of the player.

    Raises:
      ValueError if the player is not in this instance.
    """
    player = utils.check_playerid(pid)
    if player in self.players:
      return player
    raise ValueError("%s is not in instance %s" % (pid, self.key().name()))

  def check_leader(self, pid):
    """ Confirm that a player is the leader of the instance.

    Args:
      pid: A string containing the player's email address.

    Returns:
      The email address of the leader if pid contains it.

    Raises:
      ValueError if the player is not the leader of this instance.
    """
    player = utils.check_playerid(pid)
    if player == self.leader:
      return player
    raise ValueError("You must be the leader to perform this operation.")

  def add_player(self, player):
    """ Add a new player to this instance.

    Args:
      player: The email address of the player to add.

    A player can join a game instance if it is not full and either the
    instance is public or the player has been invited.  If the player
    is already in the game instance this will succeed without
    modifying the instance.

    Raises:
      ValueError if the player is not already in the game and is
      unable to join.
    """
    if player not in self.players:
      if player not in self.invited and not self.public:
        raise ValueError("%s not invited to instance %s."
                         % (player, self.key().name()))
      if self.full:
        raise ValueError("%s could not join: instance %s is full"
                         % (player, self.key().name()))
      if player in self.invited:
        self.invited.remove(player)
      self.players.append(player)
      self.set_full()
