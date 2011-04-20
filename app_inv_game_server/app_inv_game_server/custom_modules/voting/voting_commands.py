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
""" Commands for a voting application.

The commands are split into two categories. The first is for people
who are performing the voting. The second category is for the
creation and management of polls.

Voting:
Players find out about new polls by retrieving messages with types
'poll' or 'closed_poll' from the instance.

Once a player has found out about polls, they can cast votes and
get results for closed polls and polls they have already voted in.

When a player votes in a poll they immediately receive the current
results of that poll. They will be able to fetch those results until
the poll creator deletes the poll.

Poll Management:
The remaining commands are for managing polls. Polls can be
created, closed and deleted. Players can get the polls they have
created with the get my polls command.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from django.utils import simplejson
from game_server.models.message import Message
from google.appengine.ext import db

def cast_vote_command(instance, player, arguments):
  """ Cast a vote in a poll and return its current results.

  Args:
    instance: The parent GameInstance model of this poll.
    player: The player that is casting a vote.
    arguments: A two item list of the poll id and the zero
      based index of the option to select.

  Returns:
    A two item list contaning a message and the current votes
    for the poll. The message will be one of:
      Your vote was already counted in this poll.
      Poll closed to new votes.
      Vote accepted.

  Raises:
    ValueError if the vote index is larger than the number
    of options.
    ValueError if the player is not in the instance.
  """
  instance.check_player(player)
  poll = get_poll(instance, arguments[0])
  if not poll.open:
    return ['Poll closed to new votes.', poll.votes]
  if player in poll.voters:
    return ['Your vote was already counted in this poll.', poll.votes]

  try:
    poll.voters.append(player)
    vote_index = int(arguments[1])
    poll.votes[vote_index] += 1
    poll.put()
  except ValueError:
    raise ValueError('Invalid vote choice.')
  return ['Vote accepted.', poll.votes]

def get_results_command(instance, player, arguments):
  """ Gets the results of a poll.

  Args:
    instance: The parent GameInstance model of the poll.
    player: The player requesting the results.
    arguments: A one item list containing the id number of the poll.

  Returns:
    If the player has not voted in this poll and it is still open,
    this will return a single item list with a message for the
    requesting player.
    Otherwise returns a list with information about the poll. See
    get_poll_return_list for its format.

  Raises:
    ValueError if the player is not in the instance.
  """
  instance.check_player(player)
  poll = get_poll(instance, arguments[0])
  if not poll.open:
    return ['Poll is now closed.', poll.votes]
  if player in poll.voters:
    return ['You have already voted in this poll.', poll.votes]
  return ['You have not voted in this poll yet.']

def make_new_poll_command(instance, player, arguments):
  """ Make a new poll.

  Args:
    instance: The game instance to add the poll to.
    player: The email of the player creating the poll.
    arguments: A two item list containing the question and a
      second list of 2-5 options.

  Returns:
    Returns a list with information about the poll just created.
    See get_poll_return_list for its format.

  Raises:
    ValueError if the player is not in the instance.
  """
  instance.check_player(player)
  if not arguments[0]:
    raise ValueError('Question cannot be empty')
  size = len(arguments[1])
  if size < 2 or size > 5:
    raise ValueError('Incorrect number of options for poll. ' +
                     'Must be between two and five.')

  poll = Message(parent = instance, sender = player,
                 msg_type = 'poll', recipient = '')
  poll.put()
  arguments.append(poll.key().id())
  poll.content = simplejson.dumps(arguments)
  poll.votes = [0] * size
  poll.open = True
  poll.voters = ['']
  poll.put()
  return get_poll_return_list(poll)

def close_poll_command(instance, player, arguments):
  """ Close an existing poll.

  Args:
    instance: The parent GameInstance model of the poll.
    player: The email of the player closing the poll. Must be the
      poll's creator.
    arguments: A one argument list with the poll's id number.

  Returns:
    A list with information about the poll just closed. See
    get_poll_return_list for its format.

  Raises:
    ValueError if player is not the creator of the poll.
    ValueError if the player is not in the instance.
  """
  instance.check_player(player)
  poll = get_poll(instance, arguments[0])
  if poll.sender != player:
    raise ValueError('Only the person that created this poll may close it.')
  poll.open = False
  poll.msg_type = 'closed_poll'
  poll.put()
  return get_poll_return_list(poll)

def delete_poll_command(instance, player, arguments):
  """ Delete an existing poll.

  Args:
    instance: The parent GameInstance model of the poll.
    player: The email of the player closing the poll. Must be the
      poll's creator.
    arguments: A one argument list with the poll's id number.

  Returns:
    True if the deletion is successful.

  Raises:
    ValueError if player is not the creator of the poll.
    ValueError if the player is not in the instance.
  """
  instance.check_player(player)
  poll = get_poll(instance, arguments[0])
  if poll.sender != player:
    raise ValueError('Only the person that created this poll may delete it.')
  db.delete(poll)
  return [True]

def get_poll_info_command(instance, player, arguments):
  """ Get information about an existing poll.

  Args:
    instance: The parent GameInstance model of the poll.
    player: The email of the player requesting information. Must
      be the poll's creator.
    arguments: A one argument list with the poll's id number.

  Returns:
    A list with information about the poll. See
    get_poll_return_list for its format.

  Raises:
    ValueError if player is not the creator of the poll.
  Raises:
    ValueError if the player is not in the instance.
  """
  instance.check_player(player)
  poll = get_poll(instance, arguments[0])
  if poll.sender != player:
    raise ValueError('Only the person that created the poll can'
      + 'request its information.')
  return get_poll_return_list(poll)

def get_my_polls_command(instance, player, arguments = None):
  """ Get the polls created by a player in the instance.

  Args:
    instance: The parent GameInstance model of the polls.
    player: The email of the player requesting the polls.
    arguments: Not used, can be any value.

  Finds all polls created by this player.

  Returns:
    A list of two item lists with each containing the
    id number of the poll and its question.

  Raises:
    ValueError if the player is not in the instance.
  """
  instance.check_player(player)
  query = instance.get_messages_query('', '', sender = player)
  polls = query.fetch(1000)
  return [[poll.key().id(), poll.get_content()[0]] for poll in polls[::-1]]

def get_poll(instance, argument):
  """ Get a poll database model.

  Args:
    instance: The parent GameInstance database model of the poll.
    argument: The poll id argument from the server command
      arguments list.

  Returns:
    A Message database model of the poll.

  Raises:
    ValueError if argument fails to parse to an int or the
    poll doesn't exist in the database.
  """
  try:
    poll_id = int(argument)
  except ValueError:
    raise ValueError('Poll id failed to parse to a number.')

  poll_key = db.Key.from_path('Message', poll_id,
                           parent = instance.key())
  poll = db.get(poll_key)

  if poll is None:
    raise ValueError('Poll no longer exists.')
  return poll

def get_poll_return_list(poll):
  """ Get a list to return to the GameClient component for a poll.

  Args:
    poll: A Message database model that is a poll.

  Returns:
    A list with the following five items:
      The poll question.
      The poll options as a list.
      The poll id number.
      The poll votes as a list.
      Whether the poll is open.
  """
  content = poll.get_content()
  content.extend([poll.votes, poll.open])
  return content
