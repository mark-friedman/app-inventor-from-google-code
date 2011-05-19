// Copyright 2011 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android.util;

import android.graphics.Bitmap;
import android.view.View;

/**
 * Helper methods for calling methods that did not exist pre-1.6.
 *
 */
public class DonutUtil {
  public static void buildDrawingCache(View view, boolean autoScale) {
    view.buildDrawingCache(autoScale);
  }

  public static Bitmap getDrawingCache(View view, boolean autoScale) {
    return view.getDrawingCache(autoScale);
  }
}
