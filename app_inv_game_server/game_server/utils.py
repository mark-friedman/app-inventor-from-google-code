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
Utility functions for input validation and database model access.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

import re
from google.appengine.ext import db
from google.appengine.ext.db import Key

EMAIL_ADDRESS_REGEX = ("([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@"
                       "([-0-9a-zA-Z]+[.])+[a-zA-Z]{2,6}")

def get_game_model(gid):
  """ Return a Game model for the given game id.

  Args:
    gid: The game id of the Game.

  Returns:
    The database model for the specified id or None if no such model
    exists.
  """
  game_key = Key.from_path('Game', gid)
  model = db.get(game_key)
  return model

def get_instance_model(gid, iid):
  """ Return a GameInstance model for the given game and instance ids.

  Args:
    gid: The game id of the GameInstance.
    iid: The instance id of the GameInstance.

  Returns:
    The database model for the specified ids or None if the
    GameInstance doesn't exist..
  """
  instance_key = Key.from_path('Game', gid, 'GameInstance', iid)
  model = db.get(instance_key)
  return model

def check_playerid(pid, instance = None):
  """ Return a valid player id.

  Args:
    pid: A string containing the email address of the player or the
      special identified 'leader'.
    instance: (optional) The instance from which to fetch the leader
      from when pid is 'leader'.

  Returns:
    Strips the supplied player id of superfluous characters and
    returns only the email address. Also does conversion of the
    special string 'leader' to the current leader of instance.

  Raises:
    ValueError if pid does not match an email address regular
    expression.
  """
  if instance and pid.lower() == 'leader':
    pid = instance.leader

  if pid is None or pid == "":
    raise ValueError('The player identifier is blank.')
  stripped_email = re.search(EMAIL_ADDRESS_REGEX, pid)
  if stripped_email is None:
    raise ValueError('%s is not a valid email address.' % pid)
  return stripped_email.group(0)

def check_gameid(gid):
  """ Validate the game id to make sure it is not empty.

  Args:
    gid: The game id to check

  Returns:
    The game id.

  Raises:
    ValueError if the game id is the empty string or None.
  """
  if gid == "" or gid is None:
    raise ValueError('Bad Game Id: %s' % gid)
  return gid

def check_instanceid(iid):
  """ Validate the instance id to make sure it is not empty.

  Args:
    iid: The instance id to check

  Returns:
    The instance id.

  Raises:
    ValueError if the instance id is the empty string or None.
  """
  if iid == "" or iid is None:
    raise ValueError('No instance specified for request.')
  return iid

def get_boolean(value):
  """ Return a bool from value.

  Args:
    value: A string or bool representing a boolean.

  Returns:
    If value is a bool, value is returned without modification.

    If value is a string this will convert 'true' and 'false'
    (ignoring case) to their associated values.

  Raises:
    ValueError if value does not match one of the string tests and is
    not a bool.
  """
  if type(value) is not bool:
    value = value.lower()
    if value == 'true':
      value = True
    elif value == 'false':
      value = False
    else:
      raise ValueError("Boolean value was not valid")
  return value

def get_game(model):
  """ Return a Game object.

  Args:
    model: A database model that is either a GameInstance or Game.

  Returns:
    Either returns model or its parent if either of them is a Game
    object.

  Raises:
    ValueError if either model or its parent is not a Game object.
  """
  if model.__class__.__name__ == 'GameInstance':
    model = model.parent()
  if model.__class__.__name__ == 'Game':
    return model
  raise ValueError('Invalid model passed to get_game')
