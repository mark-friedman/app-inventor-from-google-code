// Copyright 2011 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.components.Component;
import com.google.devtools.simple.runtime.components.HandlesEventDispatching;

/**
 * Base class for all non-visible components.
 *
 */
@SimpleObject
public abstract class AndroidNonvisibleComponent implements Component {

  protected final Form form;

  /**
   * Creates a new AndroidNonvisibleComponent.
   *
   * @param container  container, component will be placed in
   */
  protected AndroidNonvisibleComponent(Form form) {
    this.form = form;
  }

  // Component implementation

  @Override
  public HandlesEventDispatching getDispatchDelegate() {
    return form;
  }
}
