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

from google.appengine.ext import db

from django.utils import simplejson

class Game(db.Model):
  # key_name is the game id
  instance_count = db.IntegerProperty(default=0)

  def get_public_instances(self, count = 1000):
    query = GameInstance.all()
    query.filter("public =", True)
    query.ancestor(self.key())
    query.order('-date')
    return query.fetch(count)

class GameInstance(db.Model):
  # key_name is the instance id
  # parent is Game
  players = db.StringListProperty(required=True)
  invited = db.StringListProperty(default=[])
  leader = db.StringProperty(required=True)
  date = db.DateTimeProperty(required=True, auto_now=True)
  public = db.BooleanProperty(default=False)
  full = db.BooleanProperty(default=False)
  max_players = db.IntegerProperty(default=0)
  scoreboard = db.TextProperty(default='{}')

  def put(self):
    self.set_full()
    db.Model.put(self)

  # Determines whether or not the game is full and thus can be joined.
  # This should be called whenever max_players is changed or when a 
  # player joins.
  def set_full(self):
    if self.max_players == 0 or self.max_players > len(self.players):
      self.full = False
    else:
      self.full = True

  def to_dictionary(self):
    return {'gameid' : self.parent().key().name(),
            'instanceId' : self.key().name(),
            'leader' : self.leader,
            'players' : self.players,
            'invited' : self.invited,
            'messages' : self.get_messages(),
            'public' : self.public,
            'max_players' : self.max_players,
            'scoreboard' : self.get_scoreboard()}

  def get_players(self):
    return self.players

  def query_messages(self, count, message_type, recipient):
    query = Message.all()
    if message_type != '':
      query.filter('msg_type =', message_type)
    query.filter("recipient IN", [recipient, ''])
    query.ancestor(self.key())
    query.order('-date')
    return query.fetch(count)

  def get_messages(self, count=1000, message_type='', recipient=''):
    return [message.to_dictionary() for message \
                     in self.query_messages(count, message_type, recipient)]

  # TODO implement the scoreboard as a database Model
  def get_scoreboard(self):
    board = simplejson.loads(self.scoreboard)
    for player in self.players:
      if not board.has_key(player):
        board[player] = 0
    return board

  def __str__(self):
    return simplejson.dumps(self.to_dictionary())

class Message(db.Model):
  # Need an instance id of some kind?
  # parent is GameInstance
  msg_type = db.StringProperty(required=True)
  recipient = db.EmailProperty(required=False)
  content = db.StringListProperty(required=True)
  date = db.DateTimeProperty(required=True, auto_now=True)

  def __str__(self):
    return ('game = %s, instance = %s, type = %s, recipient = %s, '
            'content = %s ' % (self.parent().parent().key().name(),
                               self.parent().key().name(), self.msg_type,
                               self.recipient, self.content))

  def to_dictionary(self):
    return {'mtype' : self.msg_type, 'mrec' : self.recipient,
            'mcont' : self.content}

  def to_json(self):
    return simplejson.dumps(self.to_dictionary())
  
