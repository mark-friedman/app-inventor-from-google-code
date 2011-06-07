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

package com.appinventor.sample.bridge;

// Import the basic modules for event dispatching, and the particular modules
// for the components used in this app
import com.google.devtools.simple.runtime.components.Component;
import com.google.devtools.simple.runtime.components.HandlesEventDispatching;
import com.google.devtools.simple.runtime.components.android.Button;
import com.google.devtools.simple.runtime.components.android.Form;
import com.google.devtools.simple.runtime.components.android.HorizontalArrangement;
import com.google.devtools.simple.runtime.components.android.Image;
import com.google.devtools.simple.runtime.components.android.Label;
import com.google.devtools.simple.runtime.components.android.Notifier;
import com.google.devtools.simple.runtime.events.EventDispatcher;

import android.util.Log;

/**
 * BridgeSample - Sample Android app that uses App Inventor components
 * 
 */

// The main class for an App Inventor app must extend Form.
// It will usually implement HandlesEventDispatching to handle any App Inventor
// events via dispatchEvent, as shown below.
public class BridgeSample extends Form implements HandlesEventDispatching {

  private static final String LOG_KEY = "AppInvTest";

  private Button button1;
  private Button button2;
  private Label label;
  private Notifier notifier;
  private int clickCount = 0;


  // The equivalent to a "main" method for App Inventor apps is the $define method.
  void $define() {

    // Component constructors take their container as an argument.  The Form is the root container
    // for an App Inventor app.

    // The Logo component lets you write messages in the system log, which can be useful 
    // for debugging.  The output is written into the Android system log (viewable with logcat).
    Log.i(LOG_KEY, "starting the app");
    HorizontalArrangement ha = new HorizontalArrangement(this);

    // Here we a placing a Button in the HorizontalArrangement so we pass that into the Button
    // constructor.
    button1 = new Button(ha);

    // Set properties of the button by calling the corresponding property setters.  These
    // correspond to the App Inventor blocks that set properties for buttons.  For detailed
    // information, see the Button.java source code.
    Log.i(LOG_KEY, "setting the properties for button1");
    button1.TextColor(COLOR_RED);
    button1.Text("Click me!");

    button2 = new Button(ha);
    Log.i(LOG_KEY, "setting the properties for button2");
    button1.TextColor(COLOR_BLUE);
    button1.FontBold(true);
    button1.FontSize(16.0f);  //font size is a float
    button2.Text("No, Click me!");


    Image image = new Image(this);
    // The string that we pass to the Picture property must name a file in the assets
    // directory for this Android project tree.
    image.Picture("happyface.png");

    Log.i(LOG_KEY, "creating the label");
    label = new Label(this);

    // Register for events.  By the second argument can be any string.    The third argument must 
    // exactly match the name of the event that you want to handle for that component.  When the event
    // happens, dispatchEvent will be called with these arguments.
    EventDispatcher.registerEventForDelegation(this, "AppInventorInJava", "Click");

    // Create a Label component, similarly as with the Button
    label = new Label(this);

    // Add a Notifier, which is a non-visible component.   Non-visible components take the
    // form as their container, just like visible components.
    notifier = new Notifier(this);  

    // Finish off the $define by initializing the click count and the label text. 
    clickCount = 0;
    showCount();

  }

  // Here is the event dispatcher for our app.  We need to Override the method for the Form 
  // superclass
  @Override
  public boolean dispatchEvent(Component component, String id, String eventName,
      Object[] args) {
    Log.i(LOG_KEY,
        String.format("dispatchEvent called: %s, %s, %s",
            id, eventName, component.toString()));
    if (component.equals(button1) && eventName.equals("Click")) {
      button1WasClicked();
      return true;
    } else if (component.equals(button2) && eventName.equals("Click")) {
      button2WasClicked();
      return true;
    } // else clauses for additional events would go here
    return false;
  }

  public void button1WasClicked() {
    Log.i(LOG_KEY, "button1 clicked");
    button1.Text("Button1 Was Clicked");
    checkCount();
  }

  private void button2WasClicked() {
    Log.i(LOG_KEY, "button2 clicked");
    // Note that we can change properties of components other than the one that was clicked.
    button1.Text("Button2 Was Clicked");
    checkCount();
  }

  // Here's the code that dispatchEvent calls for handling Button clicks.
  public void checkCount() {
    clickCount += 1;
    showCount();
    if (clickCount == 6) {
      notifier.ShowMessageDialog(
          "No more button clicks for you!",
          "Too many clicks",
      "Start over");
      clickCount = 0;
      showCount();
    }
  }

  public void showCount() {
    label.Text("You clicked " + clickCount + " times");
  }
}
