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
Contains the main function to start the App Inventor game server on
AppEngine.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from custom_modules.commands import custom_command_dict
from game_server.server import application
from game_server.autoretry_datastore import autoretry_datastore_timeouts
from google.appengine.ext.webapp.util import run_wsgi_app

def main():
  """Enables a server operation retry wrapper and runs the game server."""
  autoretry_datastore_timeouts()
  run_wsgi_app(application(custom_command_dict))

if __name__ == "__main__":
  main()
