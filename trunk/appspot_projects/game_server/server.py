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

import logging
import sys
import traceback

import iso8601
import models
import utils

from datetime import datetime
from django.utils import simplejson
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from server_commands import command_dict
from custom_commands import custom_command_dict

####################
# Module Constants #
####################
COMMAND_RESPONSE_KEY = "c"
ERROR_RESPONSE_KEY = "e"
CONTENTS_RESPONSE_KEY = "cont"

##################
# Module Methods #
##################

def run_with_response(req_handler, operation, *args, **kwargs):
  try:
    response = operation(*args, **kwargs)
    Operation_Response(contents = response).write_to_handler(req_handler)
  except ValueError, e:
    Operation_Response(contents = e.__str__(),
                       error = True).write_to_handler(req_handler)

def run_with_response_as_transaction(req_handler, operation, *args, **kwargs):
  try:
    response = db.run_in_transaction(operation, *args, **kwargs)
    Operation_Response(contents = response).write_to_handler(req_handler)
  except ValueError, e:
    Operation_Response(contents = e.__str__(),
                       error = True).write_to_handler(req_handler)

class Operation_Response():
  def __init__(self, contents, error=False):
    self.contents = contents
    self.error = error

  def write_to_handler(self, req_handler):
    if req_handler.request.get('fmt') == 'html':
      self.write_response_to_web(req_handler)
    else:
      self.write_response_to_phone(req_handler)

  def write_response_to_web(self, req_handler):
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
    req_handler.response.headers['Content-Type'] = 'application/json'
    req_handler.response.out.write(
        self.get_response_object(req_handler.request.path))
    
  def get_response_object(self, command):
    response = simplejson.dumps({COMMAND_RESPONSE_KEY : command,
                             ERROR_RESPONSE_KEY : self.error,
                             CONTENTS_RESPONSE_KEY : self.contents})
    logging.debug('response object: %s' % response)
    return response

def set_leader(gid, iid, pid, leader):
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  pid = utils.check_playerid(pid)
  leader = utils.check_playerid(leader)
  instance = utils.get_instance_model(gid, iid)
  if pid != instance.leader:
    return instance.leader
  if leader in instance.players:
    instance.leader = leader
    instance.put()
    return leader
  else:
    raise ValueError("Player %s is not a member of instance %s."
                     % (leader, iid))

def new_message(gid, iid, pid, message_type, message_recipients, message_content):
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  pid = utils.check_playerid(pid)
  instance = utils.get_instance_model(gid, iid)
  recipients_list = []
  if message_recipients != '':
    recipients_list = simplejson.loads(message_recipients)
  if not recipients_list:
    recipients_list = ['']
  content_list = simplejson.loads(message_content)
  message_list = []
  for recipient_entry in recipients_list:
    recipient_entry = utils.check_playerid(recipient_entry)
    message = models.Message(parent = instance,
                      sender = pid,
                      msg_type = message_type,
                      recipient = recipient_entry,
                      content = content_list)
    message_list.append(message)
  db.put(message_list)
  return message_list[0].to_dictionary()

def server_command(gid, iid, pid, command, arguments):
  utils.check_gameid(gid)
  pid = utils.check_playerid(pid)
  model = None
  try:
    utils.check_instanceid(iid)
    model = utils.get_instance_model(gid, iid)
  except ValueError:
    model = utils.get_game_model(gid)

  arguments = simplejson.loads(arguments)
  reply = ''

  if command in command_dict:
    reply = command_dict[command](model, pid, arguments)
    model.put()
  else:
    raise ValueError("Invalid server command: %s." % command)

  if not isinstance(reply, list):
    reply = [reply]
  return {'msender' : pid, 'mtype' : command, 'mcont': reply, 
          'mrec' : 'server_command'}

def accept_invite(gid, iid, pid):
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  pid = utils.check_playerid(pid)
  instance = utils.get_instance_model(gid, iid)
  db.run_in_transaction(accept_invite_update_instance, instance, pid)
  return get_accept_invite_response(gid, iid, pid, instance)

def accept_invite_update_instance(instance, pid):
  if pid not in instance.invited and not instance.public:
    raise ValueError("%s not invited to instance %s."
                     % (pid, instance.key().name()))
  if instance.full:
    raise ValueError("%s could not join: instance %s is full"
                     % (pid, instance.key().name()))
  if pid not in instance.players:
    instance.players.append(pid)
  if pid in instance.invited:
    instance.invited.remove(pid)
  instance.put()

def invite_player(gid, iid, pid):
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  pid = utils.check_playerid(pid)
  instance = utils.get_instance_model(gid, iid)
  if pid not in instance.invited:
    instance.invited.append(pid)
    instance.put()
  return pid
  
def new_instance(gid, iid_prefix, pid):
  """
  Creates a new instance of the specified game.  The instance id will start
  with iid_prefix, but could have any suffix.

  This should not be run inside of a transaction as it invokes db
  transactions itself.
  """
  utils.check_gameid(gid)
  pid = utils.check_playerid(pid)
  game = models.Game.get_or_insert(key_name = gid, instance_count = 0)    
  db.run_in_transaction(increment_instance_count, game)
  iid = ''
  if not iid_prefix:
    iid = make_instance_id(game, pid + 'instance')
  else:
    iid = make_instance_id(game, iid_prefix)
  db.run_in_transaction(create_game_instance, game, iid, pid)
  return iid

def increment_instance_count(game):
  game.instance_count += 1
  game.put()

def create_game_instance(game, iid, pid):
  instance = models.GameInstance(parent = game,
                          key_name = iid,
                          players = [pid],
                          leader = pid)
  instance.put()

def get_players(gid, iid):
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  instance = utils.get_instance_model(gid, iid)
  return instance.get_players()

def get_messages(gid, iid, message_type, recipient, count, time):
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  recipient = utils.check_playerid(recipient)
  instance = utils.get_instance_model(gid, iid)
  return instance.get_messages(count=count, message_type=message_type,
                               recipient=recipient, time=time)

def get_instance(gid, iid):
  utils.check_gameid(gid)
  utils.check_instanceid(iid)
  instance = utils.get_instance_model(gid, iid)
  return instance.to_dictionary()

def make_instance_id(game, instance_prefix):
  new_iid = instance_prefix.replace(' ', '')
  new_index = game.instance_count
  while models.GameInstance.get_by_key_name(new_iid, parent=game) is not None:
    new_iid = instance_prefix + str(new_index)
    new_index += 1
  return new_iid

##################
# Writer Helpers #
##################

# Send back a list of
#   - list of instances joined
#   - list of instances invited
#   - list of players of this game
#   - leader of this game
#   - instance just accepted
# This is like get_player_state, except we know that the instance exists.
# Be careful, if changing this, to coordinate with write_player_state,
# because the component uses the same code to read both responses
def get_accept_invite_response(gid, iid, pid, game):
  return {'joined' : get_instances_joined(gid, pid),
          'invited' : get_instances_invited(gid, pid)}

# The gid and pid must be good here, but the iid can be bad, because
# the player may have instances joined and instances invited even if there
# is no current game.
# Throws a value error if the game or player id's are invalid.
def get_player_state(gid, iid, pid):
  utils.check_gameid(gid)
  pid = utils.check_playerid(pid) 
  player_state = {'joined' : get_instances_joined(gid, pid),
                  'invited' : get_instances_invited(gid, pid)}
  if not iid:
    player_state['players'] = []
    player_state['leader'] = ''
  else:
    game=utils.get_instance_model(gid,iid)
    if game is None:
      player_state['players'] = []
      player_state['leader'] = ''
    else:
      player_state['players'] = game.players
      player_state['leader'] = game.leader
  return player_state

def get_instances_joined(gid, pid):
  game_model = db.get(db.Key.from_path('Game', gid))
  if game_model is None:
    return []
  query = game_model.get_joined_instances_query(pid)
  return [inst.key().name() for inst in query]

def get_instances_invited(gid, pid):
  game_model = db.get(db.Key.from_path('Game', gid))
  if game_model is None:
    return []
  query = game_model.get_invited_instances_query(pid)
  return [inst.key().name() for inst in query]

###########################
# Request Handler Classes #
###########################

class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    self.response.out.write('<html><body>')
    self.response.out.write('<h1>Game Server for Young Android GroupGame'
        'Component</h1>')
    self.write_game_list()
    self.write_methods()
    self.response.out.write('''
    <p><a href="http://appengine.google.com">
    <small><i>Go to AppEngine Administration Console</i></small>
    </a>''')
    self.response.out.write('</body></html>')

  def write_game_list(self):
    self.response.out.write('''
    <p><table border=1>
      <tr>
         <th>Created
         <th>Game</th>
         <th>Instance</th>
         <th>Players</th>
         <th>Invitees</th>
         <th>Leader</th>
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
    self.response.out.write('''
        <p />Available calls:\n
        <ul>
        <li><a href="/newinstance">/newinstance</a></li>
        <li><a href="/playerstate">/playerstate</a></li>
        <li><a href="/getplayers">/getplayers</a></li>
        <li><a href="/invite">/invite</a></li>
        <li><a href="/acceptinvite">/acceptinvite</a></li>
        <li><a href="/newmessage">/newmessage</a></li>
        <li><a href="/messages">/messages</a></li>
        <li><a href="/setleader">/setleader</a></li>
        <li><a href="/getinstance">/getinstance</a></li>
        <li><a href="/servercommand">/servercommand</a></li>
        </ul>''')

class NewInstance(webapp.RequestHandler):
  def post(self):
    logging.debug('/newinstance?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    iid = self.request.get('iid')
    pid = self.request.get('pid')
    run_with_response(self, new_instance, gid, iid, pid)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/newinstance" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>First player ID <input type="text" name="pid" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="New game">
    </form></body></html>\n''')

class InvitePlayer(webapp.RequestHandler):
  def post(self):
    logging.debug('/invite?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    iid = self.request.get('iid')
    inv = self.request.get('inv')
    run_with_response_as_transaction(self, invite_player, gid, iid, inv)

  def get(self):
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

class GetPlayers(webapp.RequestHandler):
  def post(self):
    logging.debug('/getplayers?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    iid = self.request.get('iid')
    run_with_response_as_transaction(self, get_players, gid, iid)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/getplayers" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Get players">
    </form>''')
    self.response.out.write('</body></html>\n')

class AcceptInvite(webapp.RequestHandler):
  def post(self):
    logging.debug('/acceptinvite?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    iid = self.request.get('iid')
    pid = self.request.get('pid')
    run_with_response(self, accept_invite, gid, iid, pid)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/acceptinvite" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Accept invitation">
    </form>''')
    self.response.out.write('</body></html>\n')

class NewMessage(webapp.RequestHandler):
  def post(self):
    logging.debug('/newmessage?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    pid = self.request.get('pid')
    iid = self.request.get('iid')
    message_type = self.request.get('mtype')
    message_recipients = self.request.get('mrec')
    message_content = self.request.get('mcont')
    run_with_response_as_transaction(self, new_message, gid, iid, pid, message_type,
                                     message_recipients, message_content)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/newmessage" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Message type <input type="text" name="mtype" /> </p>
       <p>Message Recipients (Json array) <input type="text" name="mrec" /> </p>
       <p>Message Contents (Json array) <input type="text" name="mcont" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Message">
    </form>''')
    self.response.out.write('''<p> Expected format for recipients: <br>
                            ["email@domain.com", "email2@domain.com"] </p>''')
    self.response.out.write('''<p> Expected format for contents: <br>
                            ["string 1", "string 2"] </p>''')
    self.response.out.write('''</body></html>\n''')

class PlayerState(webapp.RequestHandler):
  def post(self):
    logging.debug('/playerstate?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    iid = self.request.get('iid')
    pid = self.request.get('pid')
    run_with_response_as_transaction(self, get_player_state, gid, iid, pid)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/playerstate" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /></p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Get player state">
    </form>''')
    self.response.out.write('</body></html>\n')

class MessageHistory(webapp.RequestHandler):
  def post(self):
    logging.debug('/messages?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    iid = self.request.get('iid')
    message_type = self.request.get('mtype')
    recipient = self.request.get('pid')    

    count = 1000
    try:
      count = int(self.request.get('count'))
    except ValueError:
      pass

    time = datetime.min
    try:
      time_string = self.request.get('mtime')
      if time_string is not None and time_string != '':
        time = iso8601.parse_date(time_string)
    except ValueError:
      pass
    
    run_with_response_as_transaction(self, get_messages, gid, iid,
                                     message_type, recipient, count, time)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/messages" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Message type <input type="text" name="mtype" /> </p>
       <p>Email <input type="text" name="pid" /> </p>
       <p>Count <input type="text" name="count" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Get message history">
    </form></body></html>\n''')

class SetLeader(webapp.RequestHandler):
  def post(self):
    logging.debug('/setleader?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    iid = self.request.get('iid')
    leader = self.request.get('ldr')
    player = self.request.get('pid')

    run_with_response_as_transaction(self, set_leader, gid, iid, player, leader)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/setleader" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /></p>
       <p>New leader (player id) <input type="text" name="ldr" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Set leader holder">
    </form>''')
    self.response.out.write('</body></html>\n')

class ServerCommand(webapp.RequestHandler):
  def post(self):
    logging.debug('/servercommand?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    iid = self.request.get('iid')
    pid = self.request.get('pid')
    command = self.request.get('comm')
    arguments = self.request.get('cargs')
    run_with_response_as_transaction(self, server_command, gid, iid, pid,
                                     command, arguments)

  def get(self):
    self.response.out.write('''
    <html><body>
    <form action="/servercommand" method="post"
          enctype=application/x-www-form-urlencoded>
       <p>Game ID <input type="text" name="gid" /></p>
       <p>Instance ID <input type="text" name="iid" /></p>
       <p>Player ID <input type="text" name="pid" /> </p>
       <p>Command <input type="text" name="comm" /> </p>
       <p>Arguments (Json array) <input type="text" name="cargs" /> </p>
       <input type="hidden" name="fmt" value="html">
       <input type="submit" value="Message">
    </form>''')
    self.response.out.write('''</body></html>\n''')

####################################################
# Handlers not implemented in GameClient component #
####################################################

class GetInstance(webapp.RequestHandler):
  def post(self):
    logging.debug('/getinstance?%s\n|%s|' %
                  (self.request.query_string, self.request.body))
    gid = self.request.get('gid')
    iid = self.request.get('iid')
    run_with_response_as_transaction(self, get_instance, gid, iid)

  def get(self):
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

def application():
  return webapp.WSGIApplication([('/', MainPage),
                                 ('/newinstance', NewInstance),
                                 ('/invite', InvitePlayer),
                                 ('/getplayers', GetPlayers),
                                 ('/acceptinvite', AcceptInvite),
                                 ('/newmessage', NewMessage),
                                 ('/playerstate', PlayerState),
                                 ('/messages', MessageHistory),
                                 ('/setleader', SetLeader),
                                 ('/servercommand', ServerCommand),
                                 ('/getinstance', GetInstance)],
                                debug=True)

def main():
  run_wsgi_app(application())

if __name__ == "__main__":
  main()

for command in custom_command_dict.iteritems():
  if command[0] in command_dict:
    logging.debug('%s overwritten with custom command in command_dict' %
                  command[0])
  command_dict[command[0]] = command[1]
