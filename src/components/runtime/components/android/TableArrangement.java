// Copyright 2010 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.common.YaVersion;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.DesignerProperty;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.annotations.SimpleProperty;
import com.google.devtools.simple.runtime.components.Component;
import com.google.devtools.simple.runtime.components.android.util.ViewUtil;

import android.app.Activity;
import android.view.View;

/**
 * A container for components that arranges them in tabular form.
 *
 */
@DesignerComponent(version = YaVersion.TABLEARRANGEMENT_COMPONENT_VERSION,
    description = "<p>A formatting element in which to place components " +
    "that should be displayed in tabular form.</p>",
    category = ComponentCategory.ARRANGEMENTS)
@SimpleObject
public class TableArrangement extends AndroidViewComponent
    implements Component, ComponentContainer {
  private final Activity context;

  // Layout
  private final TableLayout viewLayout;

  /**
   * Creates a new TableArrangement component.
   *
   * @param container  container, component will be placed in
  */
  public TableArrangement(ComponentContainer container) {
    super(container);
    context = container.$context();

    viewLayout = new TableLayout(context, 2, 2);

    container.$add(this);
  }

  /**
   * Columns property getter method.
   *
   * @return  number of columns in this layout
   */
  @SimpleProperty(userVisible = false)
  public int Columns() {
    return viewLayout.getNumColumns();
  }

  /**
   * Columns property setter method.
   *
   * @param numColumns  number of columns in this layout
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_INTEGER,
      defaultValue = "2")
  @SimpleProperty(userVisible = false)
  public void Columns(int numColumns) {
    viewLayout.setNumColumns(numColumns);
  }

  /**
   * Rows property getter method.
   *
   * @return  number of rows in this layout
   */
  @SimpleProperty(userVisible = false)
  public int Rows() {
    return viewLayout.getNumRows();
  }

  /**
   * Rows property setter method.
   *
   * @param numRows  number of rows in this layout
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_INTEGER,
      defaultValue = "2")
  @SimpleProperty(userVisible = false)
  public void Rows(int numRows) {
    viewLayout.setNumRows(numRows);
  }

  // ComponentContainer implementation

  @Override
  public Activity $context() {
    return context;
  }

  @Override
  public Form $form() {
    return container.$form();
  }

  @Override
  public void $add(AndroidViewComponent component) {
    viewLayout.add(component);
  }

  @Override
  public void setChildWidth(AndroidViewComponent component, int width) {
    ViewUtil.setChildWidthForTableLayout(component.getView(), width);
  }

  @Override
  public void setChildHeight(AndroidViewComponent component, int height) {
    ViewUtil.setChildHeightForTableLayout(component.getView(), height);
  }

  // AndroidViewComponent implementation

  @Override
  public View getView() {
    return viewLayout.getLayoutManager();
  }
}
