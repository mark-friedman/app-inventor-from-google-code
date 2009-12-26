from google.appengine.api import mail
from django.utils import simplejson
import utils

EMAIL_SENDER = "AppInventorGameServer <aigameserver@gmail.com>"
EMAIL_SENDER_ADDRESS = "aigameserver@gmail.com"

# TODO add deleting games, original deletion code is below
# We should only allow the leader to delete a game
# Also, make sure we delete any children of instance (i.e. messages, or other stuff)
# class DeleteGame(webapp.RequestHandler):
#   def post(self):
#     logging.debug('/deletegame?%s\n|%s|' %
#                   (self.request.query_string, self.request.body))
#     gid = self.request.get('gid')
#     iid = self.request.get('iid')
#     instance.Key = db.Key.from_path('Game', gid, 'GameInstance', iid)
#     gameKey = db.Key.from_path('Game', gid)
#     game = Game.get(parentKey)
#     db.run_in_transaction(delete_instance_and_maybe_parent,
#                           gameKey, game, instanceKey)
#     MessagePattern = 'Deleted instance %s, # remaining instances = %s'
#     write_response(self, MessagePattern %
#                    (gid, iid, game.instance_count), ignore_phone=True)

# def delete_instance_and_maybe_parent(parent_key, parent_gameid, game_key):
#   parent_gameid.instance_count -= 1
#   if parent_gameid.instance_count <= 0: 
#     db_safe_delete(parent_key)
#   else: 
#     parent_gameid.put()
#   db_safe_delete(game_key)

# # a utility that guards against attempts to delete
# # the same object
# def db_safe_delete(to_delete):
#   if to_delete: db.delete(to_delete)

def send_email(instance, pid, arguments):
  message_recipient = arguments[0]
  message_content = arguments[1]
  mail.send_mail(sender=EMAIL_SENDER,
                 to=message_recipient,
                 subject=message_content[0],
                 body=message_content[1] + 
                     '\nMessage sent from AppInventorGameServer.')
  return "Email sent succesfully"

def set_public(instance, pid, arguments):
  value = utils.get_boolean(arguments[0])
  instance.public = value
  instance.put()
  return value

def set_max_players(instance, pid, arguments):
  max_players = int(arguments[0])
  instance.max_players = max_players
  instance.put()
  return max_players

def add_to_scoreboard(instance, pid, arguments):
  player = utils.check_playerid(arguments[0])
  delta = int(arguments[1])
  if player not in instance.players:
    raise ValueError("Cannot change score, %s not in instance %s"
                     % (player, instance.key().name()))
  instance.add_to_scoreboard(player, delta)
  instance.put()
  return ["%d %s" % (v, k) for k, v in instance.get_scoreboard().items()]
  
def get_public_instances(model, pid, arguments):
  game = model
  include_players = False

  if model.parent():
    game = model.parent()

  if len(arguments) > 0:
    include_players = utils.get_boolean(arguments[0])  

  count = 1000
  if len(arguments) == 2:
    count = int(arguments[1])

  public_instances = game.get_public_instances_query().fetch(count)

  if include_players:
    return [get_public_instance_string(i) for i in public_instances]
  return [i.key().name() for i in public_instances]

def get_public_instance_string(instance):
  if instance.max_players == 0:
    return '%s (%d)' % (instance.key().name(), len(instance.players))
  else:
    return '%s (%d/%d)' % (instance.key().name(), 
                           len(instance.players), instance.max_players)

def get_scoreboard(instance, pid, arguments):
  return ["%d %s" % (v, k) for k, v in instance.get_scoreboard().items()]

command_dict = {'sys_email' : send_email,
                'sys_set_public' : set_public,
                'sys_set_max_players' : set_max_players,
                'sys_change_scoreboard' : add_to_scoreboard,
                'sys_get_public_instances' : get_public_instances,
                'sys_get_scoreboard' : get_scoreboard}
