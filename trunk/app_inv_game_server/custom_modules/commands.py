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
Defines the commands available from custom modules. Custom modules
differ from built in server commands or server extensions because they
are more narrowly focused on a particular game's functionality.

Custom modules will generally be built on a per game basis and included
when game creators deploy their own App Engine servers.

This file currently includes commands for custom modules meant to be
used as examples. These can be removed to decrease load time if they
are not being used.
"""

__authors__ = ['"Bill Magnuson" <billmag@mit.edu>']

from custom_modules.androids_to_androids import ata_commands
from custom_modules.bulls_and_cows import bac_commands

custom_command_dict = {
    # Androids to Androids
    'ata_new_game' : ata_commands.new_game_command,
    'ata_submit_card' : ata_commands.submit_card_command,
    'ata_end_turn' : ata_commands.end_turn_command,

    # Bulls and Cows
    'bac_new_game' : bac_commands.new_game_command,
    'bac_guess' : bac_commands.guess_command
    }
