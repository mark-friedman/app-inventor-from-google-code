// Copyright 2007 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.common.PropertyCategory;
import com.google.devtools.simple.common.YaVersion;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.DesignerProperty;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.annotations.SimpleProperty;

import android.text.InputType;

import android.widget.EditText;

/**
 * A box in which the user can enter text.
 *
 */
@DesignerComponent(version = YaVersion.TEXTBOX_COMPONENT_VERSION,
    description = "<p>A box for the user to enter text.  The initial or " +
    "user-entered text value is in the <code>Text</code> property.  If " +
    "blank, the <code>Hint</code> property, which appears as faint text " +
    "in the box, can provide the user with guidance as to what to type.</p>" +
    "<p>Other properties affect the appearance of the text box " +
    "(<code>TextAlignment</code>, <code>BackgroundColor</code>, etc.) and " +
    "whether it can be used (<code>Enabled</code>).</p>" +
    "<p>Text boxes are usually used with the <code>Button</code> " +
    "component, with the user clicking on the button when text entry is " +
    "complete.</p>" +
    "<p>If the text entered by the user should not be displayed, use " +
    "<code>PasswordTextBox</code> instead.</p>",
    category = ComponentCategory.BASIC)
@SimpleObject
public final class TextBox extends TextBoxBase {
  /* TODO(user): this code requires Android SDK M5 or newer - we are currently on M3
  enables this when we upgrade

  // Backing for text during validation
  private String text;

  private class ValidationTransformationMethod extends TransformationMethod {
   @Override
   public CharSequence getTransformation(CharSequence source) {
     BooleanReferenceParameter accept = new BooleanReferenceParameter(false);
     Validate(source.toString, accept);

     if (accept.get()) {
       text = source.toString();
     }

     return text;
   }
 }
*/

  // If true, then accept numeric keyboard input only
  private boolean acceptsNumbersOnly;

  /**
   * Creates a new TextBox component.
   *
   * @param container  container, component will be placed in
   */
  public TextBox(ComponentContainer container) {
    super(container, new EditText(container.$context()));
    NumbersOnly(false);
  }


  /**
   * NumbersOnly property getter method.
   *
   * @return {@code true} indicates that the textbox accepts numbers only, {@code false} indicates
   *         that it accepts any text
   */
  @SimpleProperty(
      category = PropertyCategory.BEHAVIOR,
      description = "If true, then this text box accepts only numbers as keyboard input.  " +
      "Numbers can include a decimal point and an optional leading minus sign.  " +
      "This applies to keyboard input only.  Even if NumbersOnly is true, you " +
      "can use [set Text to] to enter any text at all.")
  public boolean NumbersOnly() {
    return acceptsNumbersOnly;
  }

  /**
   * NumersOnly property setter method.
   *
   * @param acceptsNumbersOnly {@code true} restricts input to numeric,
   * {@code false} allows any text
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_BOOLEAN, defaultValue = "False")
  @SimpleProperty(
      description = "If true, then this text box accepts only numbers as keyboard input.  " +
      "Numbers can include a decimal point and an optional leading minus sign.  " +
      "This applies to keyboard input only.  Even if NumbersOnly is true, you " +
      "can use [set Text to] to enter any text at all.")
  public void NumbersOnly(boolean acceptsNumbersOnly) {
    if (acceptsNumbersOnly) {
      view.setInputType(
          InputType.TYPE_CLASS_NUMBER |
          InputType.TYPE_NUMBER_FLAG_SIGNED |
          InputType.TYPE_NUMBER_FLAG_DECIMAL);
    } else {
      view.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE);
    }
    this.acceptsNumbersOnly = acceptsNumbersOnly;
  }


}
