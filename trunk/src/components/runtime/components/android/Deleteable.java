// Copyright 2010 Google. All Rights Reserved.
package com.google.devtools.simple.runtime.components.android;

/**
 * Interface for components that need to do something when they are dynamically deleted (most
 * likely by the REPL)
 *
 */
public interface Deleteable {
  void onDelete();
}
