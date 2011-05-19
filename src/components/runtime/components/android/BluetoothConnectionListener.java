// Copyright 2010 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

/**
 * Callback for receiving Bluetooth connection events
 *
 */
interface BluetoothConnectionListener {
  /**
   *
   */
  void afterConnect(BluetoothConnectionBase bluetoothConnection);

  /**
   *
   */
  void beforeDisconnect(BluetoothConnectionBase bluetoothConnection);
}
