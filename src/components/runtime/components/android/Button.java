// Copyright 2007 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.common.YaVersion;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.SimpleEvent;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.events.EventDispatcher;

/**
 * Button with the ability to launch events on initialization, focus
 * change, or a user click.  It is implemented using
 * {@link android.widget.Button}.
 *
 */
@DesignerComponent(version = YaVersion.BUTTON_COMPONENT_VERSION,
    category = ComponentCategory.BASIC,
    description = "Button with the ability to detect clicks.  Many aspects " +
    "of its appearance can be changed, as well as whether it is clickable " +
    "(<code>Enabled</code>), can be changed in the Designer or in the Blocks " +
    "Editor.")
@SimpleObject
public final class Button extends ButtonBase {

  /**
   * Creates a new Button component.
   *
   * @param container container, component will be placed in
   */
  public Button(ComponentContainer container) {
    super(container);
  }

 @Override
  public void click() {
    // Call the users Click event handler. Note that we distinguish the click() abstract method
    // implementation from the Click() event handler method.
    Click();
  }

  /**
   * Indicates a user has clicked on the button.
   */
  @SimpleEvent
  public void Click() {
    EventDispatcher.dispatchEvent(this, "Click");
  }

  @Override
  public boolean longClick() {
    // Call the users Click event handler. Note that we distinguish the longclick() abstract method
    // implementation from the LongClick() event handler method.
    return LongClick();
  }

  /**
   * Indicates a user has long clicked on the button.
   */
  @SimpleEvent
  public boolean LongClick() {
    return EventDispatcher.dispatchEvent(this, "LongClick");
  }
}
