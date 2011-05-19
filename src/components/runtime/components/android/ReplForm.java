// Copyright 2010 Google Inc. All Rights Reserved.
package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.runtime.components.android.util.ReplCommController;

import android.content.ComponentName;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.widget.Toast;

/**
 * Subclass of Form used by the 'stem cell apk', i.e. the Android app that allows communication
 * via the Repl
 *
 */
public class ReplForm extends Form {

  // Controller for the ReplCommController associated with this form
  private ReplCommController formReplCommController;

  @Override
  public void onCreate(Bundle icicle) {
    super.onCreate(icicle);
    PackageManager packageManager = this.$context().getPackageManager();
    // the following is intended to prevent the application from being restarted
    // once it has ever run (so it can be run only once after it is installed)
    packageManager.setComponentEnabledSetting(
        new ComponentName(this.getPackageName(), this.getClass().getName()),
        PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
    formReplCommController = new ReplCommController(this);
  }

  @Override
  protected void onResume() {
    super.onResume();
    formReplCommController.startListening(true /*showAlert*/);
  }

  @Override
  protected void onStop() {
    super.onStop();
    formReplCommController.stopListening(false /*showAlert*/);
  }

  @Override
  protected void onDestroy() {
    super.onDestroy();
    formReplCommController.destroy();
  }

  @Override
  protected void startNewForm(String nextFormName, String startupValue) {
    // Switching forms is not allowed in REPL (yet?).
    runOnUiThread(new Runnable() {
      public void run() {
        String message = "Switching forms is not currently supported during development.";
        Toast.makeText(ReplForm.this, message, Toast.LENGTH_LONG).show();
      }
    });
  }
}
