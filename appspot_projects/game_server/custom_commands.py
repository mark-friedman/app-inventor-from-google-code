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

from game_server.custom.androids_to_androids import deck_operations

custom_command_dict = {'ata_new_game' : deck_operations.new_androids_to_androids_game,
                       'ata_noun_card' : deck_operations.submit_card,
                       'ata_end_turn' : deck_operations.end_turn}
