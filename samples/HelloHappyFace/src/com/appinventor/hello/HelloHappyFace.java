/*
 * Copyright 2011 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.appinventor.hello;

import com.google.devtools.simple.runtime.components.HandlesEventDispatching;
import com.google.devtools.simple.runtime.components.android.Button;
import com.google.devtools.simple.runtime.components.android.Form;
import com.google.devtools.simple.runtime.components.android.Player;
import com.google.devtools.simple.runtime.events.EventDispatcher;

/**
 * HelloHappyFace - Sample Android app which uses App Inventor components
 *
 */
// The main class for an App Inventor app must extend Form.
// It will usually implement HandlesEventDispatching to handle any App Inventor
// events
public class HelloHappyFace extends Form implements HandlesEventDispatching {

  public Button button;
  private Player player;

  // The equivalent to a "main" method for App Inventor apps is the $define method.
  void $define() {
    // Component constructors take their container as an argument.  The Form is the root container
    // for an App Inventor app.
    button = new Button(this);

    // Note that the string that we pass to the image property must name a file in the assets
    // directory for this Android project tree.
    button.Image("happyface.png");

    // Register for events.  Note that by convention we use the name of the field containing
    // the component for second argument but we could use any string that would uniquely identify
    // it.  The third argument must exactly match the name of the event that you want to handle
    // for that component.
    EventDispatcher.registerEventForDelegation(this, "button", "Click");

    // Non-visible components take the Form as their container.
    player = new Player(this);
  }

  // We Override this to provide our event dispatching.
  @Override
  public void dispatchEvent(Object component, String componentName, String eventName,
                            Object[] args) {
    // There's only one event to handle in this example so we don't have to check anything.
    buttonWasClicked();
  }

  // Please see the comment above the call to registerEvent
  public void buttonWasClicked() {
    player.Vibrate(2000);
  }

}
