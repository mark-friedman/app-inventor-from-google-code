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
Contains functions to make test writing easier.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from django.utils import simplejson
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_file_stub
from google.appengine.ext import db
from google.appengine.ext.db import Key
from game_server.server import application
from game_server.models.game_instance import GameInstance
from game_server.models.game import Game
from custom_modules.commands import custom_command_dict
from webtest import TestApp

gid = 'test_gid'
firstpid = 'test@test.com'
app = TestApp(application(custom_command_dict))
players = [firstpid, '"Bob Jones" <test2@test.com>', '<test3@test.com>']

def clear_data_store():
  apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
  stub = datastore_file_stub.DatastoreFileStub('appinvgameserver',
                                               '/dev/null', '/dev/null')
  apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', stub)

def make_instance():
  response = app.post('/newinstance',
                      {'gid': gid,
                       'iid' : 'testgame',
                       'pid' : firstpid}).json
  assert response['e'] is False
  assert response['request_type'] == '/newinstance'
  return response['iid']

def make_instance_with_players():
  iid = make_instance()
  for player in players:
    add_player(iid, player)
  return iid

def add_player(instanceid, playerid):
  app.post('/invite', {'gid': gid, 'iid' : instanceid, 'inv' : playerid})
  response = app.post('/joininstance',
                      {'gid': gid, 'iid' : instanceid, 'pid' : playerid}).json
  return response['players']

def get_invited_and_joined_instances(instanceid, playerid):
  return app.post('/getinstancelists',
                  {'gid': gid,
                   'iid' : instanceid,
                   'pid' : playerid}).json['response']

def post_server_command(iid, command, args, error_expected = False,
                        pid = firstpid, gid = gid):
  response = app.post('/servercommand',
                      {'gid': gid, 'iid' : iid, 'pid' : pid,
                       'command' : command,
                       'args' : simplejson.dumps(args)}).json
  assert response['request_type'] == '/servercommand'
  if error_expected:
    assert response['e']
  else:
    assert not response['e']
    assert response['response']['type'] == command
  return response['response']

def send_new_message(iid, mtype, recipients, contents,
                     pid = firstpid, gid = gid):
  mcont = simplejson.dumps(contents)
  mrec = simplejson.dumps(recipients)
  response = app.post('/newmessage', {'gid': gid,
                                      'iid' : iid,
                                      'pid' : pid,
                                      'type' : mtype,
                                      'mrec' : mrec,
                                      'contents' : mcont}).json
  assert response['e'] is False
  if isinstance(recipients, basestring):
    assert response['response']['count'] == 1
  else:
    assert response['response']['count'] == len(recipients)
  assert response['request_type'] == '/newmessage'
  return response['response']

def get_messages(iid, mtype, time, count, pid = firstpid, gid = gid):
  response = app.post('/messages', {'gid': gid,
                                    'iid' : iid,
                                    'type' : mtype,
                                    'pid' : pid,
                                    'mtime' : time,
                                    'count' : count}).json
  assert response['e'] is False
  assert response['request_type'] == '/messages'
  assert response['response']['count'] <= count
  return response['response']['messages']

def get_instance_model(instanceid, gameid = gid):
  game_key = Key.from_path('Game', gameid, 'GameInstance', instanceid)
  model = GameInstance.get(game_key)
  return model

def get_game_model(gameid = gid):
  """ Return a Game model for the given game id.

  Args:
    gameid: The game id of the Game.

  Returns:
    The database model for the specified id or None if no such model
    exists.
  """
  return Game.get(Key.from_path('Game', gameid))
