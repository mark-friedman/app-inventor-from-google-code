// Copyright 2008 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.common.YaVersion;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.SimpleEvent;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.annotations.UsesPermissions;
import com.google.devtools.simple.runtime.components.android.util.SdkLevel;
import com.google.devtools.simple.runtime.components.util.ErrorMessages;
import com.google.devtools.simple.runtime.events.EventDispatcher;

import android.widget.AutoCompleteTextView;

/**
 * Text box using auto-completion to pick out an email address from contacts.
 *
 */

@DesignerComponent(version = YaVersion.EMAILPICKER_COMPONENT_VERSION,
    description = "<p>A text box in which a user can begin entering an email " +
    "address of a contact and be offered auto-completion.  The initial value " +
    "of the box and the value after user entry is in the <code>Text</code> " +
    "property.  If the <code>Text</code> property is initially empty, " +
    "the contents of the <code>Hint</code> property will be faintly shown " +
    "in the text box as a hint to the user.</p> " +
    "<p>Other properties affect the appearance of the text box " +
    "(<code>TextAlignment</code>, <code>BackgroundColor</code>, etc.) and " +
    "whether it can be used (<code>Enabled</code>).</p>" +
    "<p>Text boxes are usually used with the <code>Button</code> " +
    "component, with the user clicking on the button when text entry is " +
    "complete.</p>",
    category = ComponentCategory.SOCIAL)
@SimpleObject
@UsesPermissions(permissionNames = "android.permission.READ_CONTACTS")
public class EmailPicker extends TextBoxBase {

  private final EmailAddressAdapter addressAdapter;

  /**
   * Create a new EmailPicker component.
   *
   * @param container the parent container.
   */
  public EmailPicker(ComponentContainer container) {
    super(container, new AutoCompleteTextView(container.$context()));
    addressAdapter = new EmailAddressAdapter(container.$context());
    ((AutoCompleteTextView) super.view).setAdapter(addressAdapter);
  }

  /**
   * Event raised when this component is selected for input, such as by
   * the user touching it.
   */
  @SimpleEvent
  @Override
  public void GotFocus() {
    if (SdkLevel.getLevel() > SdkLevel.LEVEL_DONUT) {
      container.$form().dispatchErrorOccurredEvent(this, "GotFocus",
          ErrorMessages.ERROR_FUNCTIONALITY_NOT_SUPPORTED_EMAIL_PICKER);
    }
    EventDispatcher.dispatchEvent(this, "GotFocus");
  }
}
