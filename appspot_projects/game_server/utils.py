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

import re
from google.appengine.ext import db
from google.appengine.ext.db import Key

EMAIL_ADDRESS_REGEX = ("([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@"
                       "([-0-9a-zA-Z]+[.])+[a-zA-Z]{2,6}")

def get_game_model(gid):
  game_key = Key.from_path('Game', gid)
  model = db.get(game_key)
  if model is None:
    raise ValueError('Game %s was not found.' % gid)
  return model

def get_instance_model(gid, iid):
  instance_key = Key.from_path('Game', gid, 'GameInstance', iid)
  model = db.get(instance_key)
  if model is None:
    raise ValueError('Instance %s was not found.' % iid)
  return model

def check_playerid(pid):
  if pid is None or pid == "":
    raise ValueError('The player identifier is blank.')
  stripped_email = re.search(EMAIL_ADDRESS_REGEX, pid)
  if stripped_email is None:
    raise ValueError('%s is not a valid email address.' % pid)
  return stripped_email.group(0)

def check_gameid(gid):
  if gid == "" or gid is None:
    raise ValueError('Bad Game Id: %s' % gid)
  return gid

def check_instanceid(iid):
  if iid == "" or iid is None:
    raise ValueError('No instance specified for request.')
  return iid

def get_boolean(value):
  if type(value) is not bool:
    if value == 'true' or value == 'True':
      value = True
    elif value == 'false' or value == 'False':
      value = False
    else:
      raise ValueError("Set public boolean value was not valid")
  return value
