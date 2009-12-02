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

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_file_stub
from google.appengine.ext import db
from google.appengine.ext.db import Key
from game_server.server import application
from webtest import TestApp

gid = 'test_gid'
firstpid = 'test@test.com'
app = TestApp(application())

def clear_data_store():
  apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
  stub = datastore_file_stub.DatastoreFileStub('appinvgameserverdev',
                                               '/dev/null', '/dev/null')
  apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', stub)

def add_player(instanceid, playerid):
  app.post('/invite', {'gid': gid, 'iid' : instanceid, 'inv' : playerid})
  app.post('/acceptinvite', {'gid': gid, 'iid' : instanceid, 'pid' : playerid})

def make_instance():
  response = app.post('/newinstance',
                      {'gid': gid,
                       'iid' : 'testgame',
                       'pid' : firstpid})
  return response.json['cont']

def get_player_state(instanceid, playerid):
  return app.post('/playerstate',
                  {'gid': gid,
                   'iid' : instanceid,
                   'pid' : playerid}).json['cont']

def get_instance_model(instanceid):
  game_key = Key.from_path('Game', gid, 'GameInstance', instanceid)
  model = db.get(game_key)
  return model
