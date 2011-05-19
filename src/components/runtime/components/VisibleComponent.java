// Copyright 2008 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components;

import com.google.devtools.simple.common.PropertyCategory;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.annotations.SimpleProperty;

/**
 * Superclass of visible components in the runtime libraries.
 * <p>
 * Defines standard properties and events.
 *
 */
@SimpleObject
public abstract class VisibleComponent implements Component {
  protected VisibleComponent() {
  }

  /**
   * Width property getter method.
   *
   * @return  width property used by the layout
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE)
  public abstract int Width();

  /**
   * Width property setter method.
   *
   * @param width  width property used by the layout
   */
  @SimpleProperty
  public abstract void Width(int width);

  /**
   * Height property getter method.
   *
   * @return  height property used by the layout
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE)
  public abstract int Height();

  /**
   * Height property setter method.
   *
   * @param height  height property used by the layout
   */
  @SimpleProperty
  public abstract void Height(int height);
}
