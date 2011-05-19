// Copyright 2008 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.common.ComponentConstants;
import com.google.devtools.simple.common.PropertyCategory;
import com.google.devtools.simple.common.YaVersion;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.DesignerProperty;
import com.google.devtools.simple.runtime.annotations.SimpleEvent;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.annotations.SimpleProperty;
import com.google.devtools.simple.runtime.components.Component;
import com.google.devtools.simple.runtime.components.android.util.TextViewUtil;
import com.google.devtools.simple.runtime.events.EventDispatcher;

import android.text.method.PasswordTransformationMethod;
import android.view.View;
import android.view.View.OnFocusChangeListener;
import android.widget.EditText;

/**
 * Text box for entering passwords.
 *
 */
@DesignerComponent(version = YaVersion.PASSWORDTEXTBOX_COMPONENT_VERSION,
    description = "<p>A box for entering passwords.  This is the same as " +
    "the ordinary <code>TextBox</code> component except this does not " +
    "display the characters typed by the user.</p><p>The value of the text " +
    "in the box can be found or set through the <code>Text</code> property. " +
    "If blank, the <code>Hint</code> property, which appears as faint text " +
    "in the box, can provide the user with guidance as to what to type.</p> " +
    "<p>Text boxes are usually used with the <code>Button</code> " +
    "component, with the user clicking on the button when text entry is " +
    "complete.</p>",
    category = ComponentCategory.BASIC)
@SimpleObject
public final class PasswordTextBox extends AndroidViewComponent implements
    OnFocusChangeListener {

  private final EditText view;

  // Backing for text alignment
  private int textAlignment;

  // Backing for background color
  private int backgroundColor;

  // Backing for font typeface
  private int fontTypeface;

  // Backing for font bold
  private boolean bold;

  // Backing for font italic
  private boolean italic;

  // Backing for hint text
  private String hint;

  // Backing for text color
  private int textColor;

  /**
   * Creates a new TextBox component.
   *
   * @param container  container, component will be placed in
   */
  public PasswordTextBox(ComponentContainer container) {
    super(container);
    view = new EditText(container.$context());

    // Listen to focus changes
    view.setOnFocusChangeListener(this);

    // Add a transformation method to hide password text.
    view.setTransformationMethod(new PasswordTransformationMethod());

    // Adds the component to its designated container
    container.$add(this);

    container.setChildWidth(this, ComponentConstants.TEXTBOX_PREFERRED_WIDTH);

    // Initialization of default property values.
    TextAlignment(Component.ALIGNMENT_NORMAL);
    BackgroundColor(Component.COLOR_NONE);
    Enabled(true);
    fontTypeface = Component.TYPEFACE_DEFAULT;
    TextViewUtil.setFontTypeface(view, fontTypeface, bold, italic);
    FontSize(Component.FONT_DEFAULT_SIZE);
    Hint("");
    Text("");
    TextColor(Component.COLOR_BLACK);
  }

  @Override
  public View getView() {
    return view;
  }

  /**
   * Default GotFocus event handler.
   */
  @SimpleEvent
  public void GotFocus() {
    EventDispatcher.dispatchEvent(this, "GotFocus");
  }

  /**
   * Default LostFocus event handler.
   */
  @SimpleEvent
  public void LostFocus() {
    EventDispatcher.dispatchEvent(this, "LostFocus");
  }

  /**
   * Returns the alignment of the password textbox's text: center, normal
   * (e.g., left-justified if text is written left to right), or
   * opposite (e.g., right-justified if text is written left to right).
   *
   * @return  one of {@link Component#ALIGNMENT_NORMAL},
   *          {@link Component#ALIGNMENT_CENTER} or
   *          {@link Component#ALIGNMENT_OPPOSITE}
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE,
      userVisible = false)
  public int TextAlignment() {
    return textAlignment;
  }

  /**
   * Specifies the alignment of the password textbox's text: center, normal
   * (e.g., left-justified if text is written left to right), or
   * opposite (e.g., right-justified if text is written left to right).
   *
   * @param alignment  one of {@link Component#ALIGNMENT_NORMAL},
   *                   {@link Component#ALIGNMENT_CENTER} or
   *                   {@link Component#ALIGNMENT_OPPOSITE}
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_TEXTALIGNMENT,
      defaultValue = Component.ALIGNMENT_NORMAL + "")
  @SimpleProperty(
      userVisible = false)
  public void TextAlignment(int alignment) {
    this.textAlignment = alignment;
    TextViewUtil.setAlignment(view, alignment, false);
  }

  /**
   * Returns the password textbox's background color as an alpha-red-green-blue
   * integer.
   *
   * @return  background RGB color with alpha
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE)
  public int BackgroundColor() {
    return backgroundColor;
  }

  /**
   * Specifies the password textbox's background color as an alpha-red-green-blue
   * integer.
   *
   * @param argb  background RGB color with alpha
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_COLOR,
      defaultValue = Component.DEFAULT_VALUE_COLOR_NONE)
  @SimpleProperty
  public void BackgroundColor(int argb) {
    backgroundColor = argb;
    if (argb != Component.COLOR_DEFAULT) {
      TextViewUtil.setBackgroundColor(view, argb);
    } else {
      TextViewUtil.setBackgroundColor(view, Component.COLOR_NONE);
    }
  }

  /**
   * Returns true if the password textbox is active and useable.
   *
   * @return  {@code true} indicates enabled, {@code false} disabled
   */
  @SimpleProperty(
      category = PropertyCategory.BEHAVIOR)
  public boolean Enabled() {
    return TextViewUtil.isEnabled(view);
  }

  /**
   * Specifies whether the password textbox should be active and useable.
   *
   * @param enabled  {@code true} for enabled, {@code false} disabled
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_BOOLEAN,
      defaultValue = "True")
  @SimpleProperty
  public void Enabled(boolean enabled) {
    TextViewUtil.setEnabled(view, enabled);
  }

  /**
   * Returns true if the password textbox's text should be bold.
   * If bold has been requested, this property will return true, even if the
   * font does not support bold.
   *
   * @return  {@code true} indicates bold, {@code false} normal
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE,
      userVisible = false)
  public boolean FontBold() {
    return bold;
  }

  /**
   * Specifies whether the password textbox's text should be bold.
   * Some fonts do not support bold.
   *
   * @param bold  {@code true} indicates bold, {@code false} normal
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_BOOLEAN,
      defaultValue = "False")
  @SimpleProperty(
      userVisible = false)
  public void FontBold(boolean bold) {
    this.bold = bold;
    TextViewUtil.setFontTypeface(view, fontTypeface, bold, italic);
  }

  /**
   * Returns true if the password textbox's text should be italic.
   * If italic has been requested, this property will return true, even if the
   * font does not support italic.
   *
   * @return  {@code true} indicates italic, {@code false} normal
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE,
      userVisible = false)
  public boolean FontItalic() {
    return italic;
  }

  /**
   * Specifies whether the password textbox's text should be italic.
   * Some fonts do not support italic.
   *
   * @param italic  {@code true} indicates italic, {@code false} normal
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_BOOLEAN,
      defaultValue = "False")
  @SimpleProperty(userVisible = false)
  public void FontItalic(boolean italic) {
    this.italic = italic;
    TextViewUtil.setFontTypeface(view, fontTypeface, bold, italic);
  }

  /**
   * Returns the password textbox's text's font size, measured in pixels.
   *
   * @return  font size in pixel
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE,
      userVisible = false)
  public float FontSize() {
    return TextViewUtil.getFontSize(view);
  }

  /**
   * Specifies the password textbox's text's font size, measured in pixels.
   *
   * @param size  font size in pixel
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_FLOAT,
      defaultValue = Component.FONT_DEFAULT_SIZE + "")
  @SimpleProperty(
      userVisible = false)
  public void FontSize(float size) {
    TextViewUtil.setFontSize(view, size);
  }

  /**
   * Returns the password textbox's text's font face as default, serif, sans
   * serif, or monospace.
   *
   * @return  one of {@link Component#TYPEFACE_DEFAULT},
   *          {@link Component#TYPEFACE_SERIF},
   *          {@link Component#TYPEFACE_SANSSERIF} or
   *          {@link Component#TYPEFACE_MONOSPACE}
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE,
      userVisible = false)
  public int FontTypeface() {
    return fontTypeface;
  }

  /**
   * Specifies the password textbox's text's font face as default, serif, sans
   * serif, or monospace.
   *
   * @param typeface  one of {@link Component#TYPEFACE_DEFAULT},
   *                  {@link Component#TYPEFACE_SERIF},
   *                  {@link Component#TYPEFACE_SANSSERIF} or
   *                  {@link Component#TYPEFACE_MONOSPACE}
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_TYPEFACE,
      defaultValue = Component.TYPEFACE_DEFAULT + "")
  @SimpleProperty(
      userVisible = false)
  public void FontTypeface(int typeface) {
    fontTypeface = typeface;
    TextViewUtil.setFontTypeface(view, fontTypeface, bold, italic);
  }

  /**
   * Hint property getter method.
   *
   * @return  hint text
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE)
  public String Hint() {
    return hint;
  }

  /**
   * Hint property setter method.
   *
   * @param hint  hint text
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_STRING,
      defaultValue = "")
  @SimpleProperty
  public void Hint(String hint) {
    this.hint = hint;
    view.setHint(hint);
    view.invalidate();
  }

  /**
   * Returns the password textbox contents.
   *
   * @return  text box contents
   */
  @SimpleProperty(
      category = PropertyCategory.BEHAVIOR)
  public String Text() {
    return TextViewUtil.getText(view);
  }

  /**
   * Specifies the password textbox contents.
   *
   * @param text  new text in text box
   */
  @SimpleProperty
  public void Text(String text) {
    TextViewUtil.setText(view, text);
  }

  /**
   * Returns the password textbox's text color as an alpha-red-green-blue
   * integer.
   *
   * @return  text RGB color with alpha
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE)
  public int TextColor() {
    return textColor;
  }

  /**
   * Specifies the password textbox's text color as an alpha-red-green-blue
   * integer.
   *
   * @param argb  text RGB color with alpha
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_COLOR,
      defaultValue = Component.DEFAULT_VALUE_COLOR_BLACK)
  @SimpleProperty
  public void TextColor(int argb) {
    textColor = argb;
    if (argb != Component.COLOR_DEFAULT) {
      TextViewUtil.setTextColor(view, argb);
    } else {
      TextViewUtil.setTextColor(view, Component.COLOR_BLACK);
    }
  }

  // OnFocusChangeListener implementation
  @Override
  public void onFocusChange(View previouslyFocused, boolean gainFocus) {
    if (gainFocus) {
      GotFocus();
    } else {
      LostFocus();
    }
  }
}
