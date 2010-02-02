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
""" The Message database model class and associated methods."""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from datetime import datetime
from django.utils import simplejson
from game_server import iso8601
from google.appengine.ext import db

class Message(db.Expando):
  """ A model for a message sent to a player in a game instance.

  Messages are used to pass information from player to player and from
  server to player. A Message's parent is the GameInstance which it is
  created for.

  Attributes:
    msg_type: A string that acts as a key for the message.
    recipient (optional): The intended recipient of this message.
    content: JSON string that represents the contents of the message.
    date: The date of creation, automatically set upon instantiation.
    sender: A string describing the creator of the message.
  """
  msg_type = db.StringProperty(required=True)
  recipient = db.StringProperty(required=False)
  content = db.TextProperty(required=False)
  date = db.DateTimeProperty(required=True, auto_now_add=True)
  sender = db.StringProperty(required=True)

  def to_dictionary(self):
    """ Return a Python dictionary of the message.

    Returns a dictionary of the message:
      type: msg_type
      mrec: recipient
      contents: the Python representation of the content JSON string.
      mtime: The iso8601 string representation of the creation time of
        the message.
      msender: sender
    """
    return {'type' : self.msg_type, 'mrec' : self.recipient,
            'contents' : simplejson.loads(self.content),
            'mtime' : self.date.isoformat(),
            'msender' : self.sender}

  def to_json(self):
    """ Return a json representation of the dictionary of this message. """
    return simplejson.dumps(self.to_dictionary())

  def get_content(self):
    """ Return the Python representation of the contents of this message. """
    return simplejson.loads(self.content)
