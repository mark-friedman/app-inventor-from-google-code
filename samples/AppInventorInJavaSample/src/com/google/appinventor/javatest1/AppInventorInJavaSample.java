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

package com.google.appinventor.javatest1;

import com.google.devtools.simple.runtime.components.HandlesEventDispatching;
import com.google.devtools.simple.runtime.components.android.Button;
import com.google.devtools.simple.runtime.components.android.Form;
import com.google.devtools.simple.runtime.components.android.HorizontalArrangement;
import com.google.devtools.simple.runtime.components.android.Image;
import com.google.devtools.simple.runtime.events.EventDispatcher;

import android.util.Log;

/**
 */
// The main class for an App Inventor app must extend Form
public class AppInventorInJavaSample extends Form implements HandlesEventDispatching {

  private static final String LOG_KEY = "AITest";
  public Button button1;
  private MyButton button3;

  // The equivalent to a "main" method for App Inventor apps is the $define method.
  void $define() {
    // Component constructors take their container as an argument.  The Form is the root container
    // for an App Inventor app.
    HorizontalArrangement ha = new HorizontalArrangement(this);
    Log.i(LOG_KEY, "creating a button");
    // Here we a placing a Button in the HorizontalArrangement so we pass that into the Button
    // constructor.
    button1 = new Button(ha);
    Log.i(LOG_KEY, "setting the button text");
    button1.Text("Hello!");

    // If you don't necessarily need to have a field associated with a component.
    Button button2 = new Button(ha);
    button2.Text("Does Nothing.");

    // Now let's try and add one of the newly defined MyButton components.
    button3 = new MyButton(this);

    Image image = new Image(this);
    // The string that we pass to the Picture property must name a file in the assets
    // directory for this Android project tree.
    image.Picture("happyface.png");

    // Register for events.  The second argument is just an identifier.  The third argument must
    // exactly match the name of the event that you want to handle.
    EventDispatcher.registerEventForDelegation(this, "AppInventorInJava", "Click");
  }

  @Override
  public void dispatchEvent(Object component, String id, String eventName,
                            Object[] args) {
    Log.i(LOG_KEY,
          String.format("dispatchEvent called: %s, %s, %s",
                        id, eventName, component.toString()));
    if (component.equals(button1) && eventName.equals("Click")) {
      button1WasClicked();
    } else if (component.equals(button3) && eventName.equals("Click")) {
      button3WasClicked();
    } // else clauses for other events would go here
  }

  private void button3WasClicked() {
    Log.i(LOG_KEY, "button3 clicked");
    // Note that we can change properties of components other than the one that was clicked.
    button1.Text("Button3 Was Clicked");
  }

  // Please see the comment above for the call to registerEvent.
  public void button1WasClicked() {
    Log.i(LOG_KEY, "button1 clicked");
    button1.Text("Button1 Was Clicked");
  }
}
