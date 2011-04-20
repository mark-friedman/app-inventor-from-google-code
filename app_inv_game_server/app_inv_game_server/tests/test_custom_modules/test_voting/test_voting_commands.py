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
""" Provides basic utility functions for the voting module. """

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from tests import test_utils
from google.appengine.ext.db import Key
from game_server.models.message import Message

gid = test_utils.gid
firstpid = test_utils.firstpid
app = test_utils.app

question = 'I can haz cheezburger?'
choices = ['yes', 'nom']

def setUp():
  test_utils.clear_data_store()

def test_make_poll():
  iid = test_utils.make_instance()
  contents = test_utils.post_server_command(
      iid, 'vot_new_poll', [question, choices])['contents']
  poll_id = contents[2]
  assert contents == [question, choices, poll_id, [0] * len(choices), True]

def test_close_poll():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  contents = test_utils.post_server_command(iid, 'vot_close_poll',
                                            [poll_id])['contents']
  assert contents == [question, choices, poll_id, [0] * len(choices), False]
  poll = get_poll(iid, poll_id)
  assert poll.msg_type == 'closed_poll'
  assert poll.open == False

def test_delete_poll():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  contents = test_utils.post_server_command(iid, 'vot_delete_poll',
                                            [poll_id])['contents']
  assert contents == [True]
  poll = get_poll(iid, poll_id)
  assert not poll

def test_get_only_my_polls():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  test_utils.add_player(iid, 'other@gmail.com')
  make_poll(iid, pid = 'other@gmail.com')
  contents = test_utils.post_server_command(iid, 'vot_get_my_polls',
                                            [])['contents']
  assert len(contents) == 1
  assert contents[0] == [poll_id, question]

def test_get_poll_information():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  contents = test_utils.post_server_command(iid, 'vot_get_poll_info',
                                            [poll_id, 1])['contents']
  assert contents == [question, choices, poll_id, [0] * len(choices), True]

def test_cast_vote():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  contents = test_utils.post_server_command(iid, 'vot_cast_vote',
                                            [poll_id, 1])['contents']
  assert contents[1] == [0, 1]
  assert contents[0] == 'Vote accepted.'

def test_cast_vote_twice():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  test_utils.post_server_command(iid, 'vot_cast_vote',
                                 [poll_id, 1])['contents']
  contents = test_utils.post_server_command(iid, 'vot_cast_vote',
                                            [poll_id, 1])['contents']
  assert contents[1] == [0, 1]
  assert contents[0] == 'Your vote was already counted in this poll.'

def test_cast_vote_to_closed_poll():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  test_utils.post_server_command(iid, 'vot_close_poll',
                                 [poll_id])['contents']
  contents = test_utils.post_server_command(iid, 'vot_cast_vote',
                                            [poll_id, 1])['contents']
  assert contents[1] == [0, 0]
  assert contents[0] == 'Poll closed to new votes.'

def test_get_results():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  test_utils.post_server_command(iid, 'vot_cast_vote',
                                 [poll_id, 1])['contents']
  contents = test_utils.post_server_command(iid, 'vot_get_results',
                                            [poll_id])['contents']
  assert contents == ['You have already voted in this poll.', [0, 1]]

def test_get_results_before_voting():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  contents = test_utils.post_server_command(iid, 'vot_get_results',
                                            [poll_id])['contents']
  assert contents == ['You have not voted in this poll yet.']

def test_get_reslts_before_voting_in_closed_poll():
  iid = test_utils.make_instance()
  poll_id = make_poll(iid)
  test_utils.post_server_command(iid, 'vot_close_poll',
                                 [poll_id])['contents']
  contents = test_utils.post_server_command(iid, 'vot_get_results',
                                            [poll_id])['contents']
  assert contents == ['Poll is now closed.', [0, 0]]

def make_poll(iid, pid = firstpid):
  return test_utils.post_server_command(
      iid, 'vot_new_poll', [question, choices],
      pid = pid)['contents'][2]

def get_poll(iid, poll_id):
  key = Key.from_path('Game', gid, 'GameInstance', iid, 'Message', poll_id)
  return Message.get(key)

def get_new_poll(iid):
  poll_id = test_utils.post_server_command(
      iid, 'vot_new_poll', [questions, choices])['contents'][2]
  return get_poll(iid, poll_id)
