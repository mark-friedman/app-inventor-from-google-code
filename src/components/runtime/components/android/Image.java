// Copyright 2007 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.common.PropertyCategory;
import com.google.devtools.simple.common.YaVersion;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.DesignerProperty;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.annotations.SimpleProperty;
import com.google.devtools.simple.runtime.annotations.UsesPermissions;
import com.google.devtools.simple.runtime.components.android.util.AnimationUtil;
import com.google.devtools.simple.runtime.components.android.util.MediaUtil;
import com.google.devtools.simple.runtime.components.android.util.ViewUtil;

import android.graphics.drawable.Drawable;
import android.util.Log;
import android.view.View;
import android.widget.ImageView;

import java.io.IOException;

/**
 * Component for displaying images and animations.
 *
 */
@DesignerComponent(version = YaVersion.IMAGE_COMPONENT_VERSION,
    category = ComponentCategory.BASIC,
    description = "Component for displaying images.  The picture to display, " +
    "and other aspects of the Image's appearance, can be specified in the " +
    "Designer or in the Blocks Editor.")
@SimpleObject
@UsesPermissions(permissionNames = "android.permission.INTERNET")
public final class Image extends AndroidViewComponent {

  private final ImageView view;

  private String picturePath = "";  // Picture property

  /**
   * Creates a new Image component.
   *
   * @param container  container, component will be placed in
   */
  public Image(ComponentContainer container) {
    super(container);
    view = new ImageView(container.$context()) {
      @Override
      public boolean verifyDrawable(Drawable dr) {
        super.verifyDrawable(dr);
        // TODO(user): multi-image animation
        return true;
      }
    };

    // Adds the component to its designated container
    container.$add(this);
    view.setFocusable(true);
  }

  @Override
  public View getView() {
    return view;
  }

  /**
   * Returns the path of the image's picture.
   *
   * @return  the path of the image's picture
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE)
  public String Picture() {
    return picturePath;
  }

  /**
   * Specifies the path of the image's picture.
   *
   * <p/>See {@link MediaUtil#determineMediaSource} for information about what
   * a path can be.
   *
   * @param path  the path of the image's picture
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_ASSET,
      defaultValue = "")
  @SimpleProperty
  public void Picture(String path) {
    picturePath = (path == null) ? "" : path;

    Drawable drawable;
    try {
      drawable = MediaUtil.getDrawable(container.$form(), picturePath);
    } catch (IOException ioe) {
      Log.e("Image", "Unable to load " + picturePath);
      drawable = null;
    }

    ViewUtil.setImage(view, drawable);
  }


  /**
   * Animation property setter method.
   *
   * @see AnimationUtil
   *
   * @param animation  animation kind
   */
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE)
  public void Animation(String animation) {
    AnimationUtil.ApplyAnimation(view, animation);
  }
}
