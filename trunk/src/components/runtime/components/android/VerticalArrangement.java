// Copyright 2009 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.common.ComponentConstants;
import com.google.devtools.simple.common.YaVersion;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.SimpleObject;

/**
 * A vertical arrangement of components
 *
 */

@DesignerComponent(version = YaVersion.VERTICALARRANGEMENT_COMPONENT_VERSION,
    description = "<p>A formatting element in which to place components " +
    "that should be displayed one below another.  (The first child component " +
    "is stored on top, the second beneath it, etc.)  If you wish to have " +
    "components displayed next to one another, use " +
    "<code>HorizontalArrangement</code> instead.</p>",
    category = ComponentCategory.ARRANGEMENTS)
@SimpleObject
public class VerticalArrangement extends HVArrangement {

  public VerticalArrangement(ComponentContainer container) {
    super(container, ComponentConstants.LAYOUT_ORIENTATION_VERTICAL);
  }

}
