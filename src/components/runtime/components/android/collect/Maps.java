// Copyright 2008 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android.collect;

import java.util.HashMap;

/**
 * Provides static methods for creating mutable {@code Maps} instances easily.
 *
 * Note: This was copied from the com.google.android.collect.Lists class
 *
 */
public class Maps {
  /**
   * Creates a {@code HashMap} instance.
   *
   * @return a newly-created, initially-empty {@code HashMap}
   */
  public static <K, V> HashMap<K, V> newHashMap() {
    return new HashMap<K, V>();
  }
}
