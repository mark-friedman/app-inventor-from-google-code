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

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.SimpleEvent;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.components.android.ButtonBase;
import com.google.devtools.simple.runtime.components.android.ComponentContainer;
import com.google.devtools.simple.runtime.events.EventDispatcher;

/**
 */
// The DesignerComponent annotation really only matters when the component is used within the
// AppInventor IDE but it's good to include it, in preparation for that.
@DesignerComponent(version = 1,
    category = ComponentCategory.BASIC,
    description = "Button whose Text is initially 'This is My Button!'")
// The SimpleObject annotation is required for all component classes
@SimpleObject
public class MyButton extends ButtonBase {

  /**
   * Creates a new component with a different default text.
   *
   * @param container container, component will be placed in
   */
  public MyButton(ComponentContainer container) {
    super(container);
    // Set our text property.
    Text("This is My Button!!");
  }

  // Some ButtonBase subclasses want to do more complex things, but here we just define a basic
  // behavior which just invokes a Click handler that can be registered in the Form object.
  @Override
  public void click() {
    // Call the users Click event handler. Note that we distinguish the click() abstract method
    // implementation from the Click() event handler method.
    Click();
  }

  /**
   * Indicates a user has clicked on the button.
   */
  // The SimpleObject annotation is required for all event handling methods
  @SimpleEvent(description = "Handler for click events.")
  public void Click() {
    // This is what causes the App Inventor runtime to invoke the "Click" event for this object.
    EventDispatcher.dispatchEvent(this, "Click");
  }
}
