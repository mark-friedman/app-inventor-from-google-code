import re
from google.appengine.ext import db
from google.appengine.ext.db import Key

EMAIL_ADDRESS_REGEX = ("([0-9a-zA-Z]+[-._+&amp;])*[0-9a-zA-Z]+@"
                       "([-0-9a-zA-Z]+[.])+[a-zA-Z]{2,6}")

def get_instance_model(gid, iid):
  game_key = Key.from_path('Game', gid, 'GameInstance', iid)
  model = db.get(game_key)
  if model is None:
    raise ValueError('Instance %s not found.' % iid)
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
    raise ValueError('No instance specified for request.' % iid)
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
