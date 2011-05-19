// Copyright 2009 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.common.ComponentConstants;
import com.google.devtools.simple.common.YaVersion;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.SimpleObject;

/**
 * A horizontal arrangement of components
 *
 */
@DesignerComponent(version = YaVersion.HORIZONTALARRANGEMENT_COMPONENT_VERSION,
    description = "<p>A formatting element in which to place components " +
    "that should be displayed from left to right.  If you wish to have " +
    "components displayed one over another, use " +
    "<code>VerticalArrangement</code> instead.</p>",
    category = ComponentCategory.ARRANGEMENTS)
@SimpleObject
public class HorizontalArrangement extends HVArrangement {
  public HorizontalArrangement(ComponentContainer container) {
    super(container, ComponentConstants.LAYOUT_ORIENTATION_HORIZONTAL);
  }

}
