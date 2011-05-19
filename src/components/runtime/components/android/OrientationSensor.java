// Copyright 2008 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components.android;

import com.google.devtools.simple.common.ComponentCategory;
import com.google.devtools.simple.common.PropertyCategory;
import com.google.devtools.simple.common.YaVersion;
import com.google.devtools.simple.runtime.annotations.DesignerComponent;
import com.google.devtools.simple.runtime.annotations.DesignerProperty;
import com.google.devtools.simple.runtime.annotations.SimpleEvent;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.annotations.SimpleProperty;
import com.google.devtools.simple.runtime.events.EventDispatcher;

import android.content.Context;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.util.Log;

import java.util.List;

/**
 * Sensor that can measure absolute orientation in 3 dimensions.
 *
 * TODO(user): This implementation does not correct for acceleration
 * of the phone.  Make a better version that does this.
 */
@DesignerComponent(version = YaVersion.ORIENTATIONSENSOR_COMPONENT_VERSION,
    description = "<p>Non-visible component providing information about the " +
    "device's physical orientation in three dimensions: <ul> " +
    "<li> <strong>Roll</strong>: 0 degrees when the device is level, increases to " +
    "     90 degrees as the device is tilted up on its left side, and " +
    "     decreases to &minus;90 degrees when the device is tilted up on its right side. " +
    "     </li> " +
    "<li> <strong>Pitch</strong>: 0 degrees when the device is level, up to " +
    "     90 degrees as the device is tilted so its top is pointing down, " +
    "     up to 180 degrees as it gets turned over.  Similarly, as the device " +
    "     is tilted so its bottom points down, pitch decreases to &minus;90 " +
    "     degrees, then further decreases to &minus;180 degrees as it gets turned all the way " +
    "     over.</li> " +
    "<li> <strong>Yaw</strong>: 0 degrees when the top of the device is " +
    "     pointing north, 90 degrees when it is pointing east, 180 degrees " +
    "     when it is pointing south, 270 degrees when it is pointing west, " +
    "     etc.</li></ul>" +
    "     These measurements assume that the device itself is not moving.</p>",
    category = ComponentCategory.SENSORS,
    nonVisible = true,
    iconName = "images/orientationsensor.png")

@SimpleObject
public class OrientationSensor extends AndroidNonvisibleComponent
    implements SensorEventListener, Deleteable {
  private final SensorManager sensorManager;
  private Sensor orientationSensor;
  private boolean enabled;
  private float yaw;
  private float pitch;
  private float roll;
  private int accuracy;

  /**
   * Creates a new OrientationSensor component.
   *
   * @param container  ignored (because this is a non-visible component)
   */
  public OrientationSensor(ComponentContainer container) {
    super(container.$form());
    sensorManager =
      (SensorManager) container.$context().getSystemService(Context.SENSOR_SERVICE);
    orientationSensor = sensorManager.getDefaultSensor(Sensor.TYPE_ORIENTATION);
    sensorManager.registerListener(this, orientationSensor, SensorManager.SENSOR_DELAY_GAME);
    enabled = true;
  }

  // Events

  /**
   * Default OrientationChanged event handler.
   *
   * <p>This event is signalled when the device's orientation has changed.  It
   * reports the new values of yaw, pich, and roll, and it also sets the Yaw, Pitch,
   * and roll properties.</p>
   * <p>Yaw is the compass heading in degrees, pitch indicates how the device
   * is tilted from top to bottom, and roll indicates how much the device is tilted from
   * side to side.</p>
   */
  @SimpleEvent
  public void OrientationChanged(float yaw, float pitch, float roll) {
    EventDispatcher.dispatchEvent(this, "OrientationChanged", yaw, pitch, roll);
  }

  // Properties

  /**
   * Available property getter method (read-only property).
   *
   * @return {@code true} indicates that an orientation sensor is available,
   *         {@code false} that it isn't
   */
  @SimpleProperty(category = PropertyCategory.BEHAVIOR)
  public boolean Available() {
    List<Sensor> sensors = sensorManager.getSensorList(Sensor.TYPE_ORIENTATION);
    return (sensors.size() > 0);
  }

  /**
   * Enabled property getter method.
   *
   * @return {@code true} indicates that the sensor generates events,
   *         {@code false} that it doesn't
   */
  @SimpleProperty(category = PropertyCategory.BEHAVIOR)
  public boolean Enabled() {
    return enabled;
  }

  /**
   * Enabled property setter method.
   *
   * @param enabled  {@code true} enables sensor event generation,
   *                 {@code false} disables it
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_BOOLEAN,
      defaultValue = "True")
  @SimpleProperty
  public void Enabled(boolean enabled) {
    this.enabled = enabled;
  }

  /**
   * Pitch property getter method (read-only property).
   *
   * <p>To return meaningful values the sensor must be enabled.</p>
   *
   * @return  current pitch
   */
  @SimpleProperty(category = PropertyCategory.BEHAVIOR)
  public float Pitch() {
    return pitch;
  }

  /**
   * Roll property getter method (read-only property).
   *
   * <p>To return meaningful values the sensor must be enabled.</p>
   *
   * @return  current roll
   */
  @SimpleProperty(category = PropertyCategory.BEHAVIOR)
  public float Roll() {
    return roll;
  }

  /**
   * Yaw property getter method (read-only property).
   *
   * <p>To return meaningful values the sensor must be enabled.</p>
   *
   * @return  current yaw
   */
  @SimpleProperty(category = PropertyCategory.BEHAVIOR)
  public float Yaw() {
    return yaw;
  }

  /**
   * Angle property getter method (read-only property).  Specifically, this
   * provides the angle in which the orientation sensor is tilted, treating
   * {@link #Roll()} as the x-coordinate and {@link #Pitch()} as the
   * y-coordinate.  For the amount of the tilt, use {@link #Magnitude()}.
   *
   * <p>To return meaningful values the sensor must be enabled.</p>
   *
   * @return the angle in degrees
   */
  @SimpleProperty(category = PropertyCategory.BEHAVIOR)
  public float Angle() {
    return (float) (180.0 - Math.toDegrees(Math.atan2(pitch, roll)));
  }

  /**
   * Magnitude property getter method (read-only property).  Specifically, this
   * returns a number between 0 and 1, indicating how much the device
   * is tilted.  For the angle of tilt, use {@link #Angle()}.
   *
   * <p>To return meaningful values the sensor must be enabled.</p>
   *
   * @return the magnitude of the tilt, from 0 to 1
   */
  @SimpleProperty(category = PropertyCategory.BEHAVIOR)
  public float Magnitude() {
    // Limit pitch and roll to 90; otherwise, the phone is upside down.
    // The official documentation falsely claims that the range of pitch and
    // roll is [-90, 90].  If the device is upside-down, it can range from
    // -180 to 180.  We restrict it to the range [-90, 90].
    // With that restriction, if the pitch and roll angles are P and R, then
    // the force is given by 1 - cos(P)cos(R).  I have found a truly wonderful
    // proof of this theorem, but the margin enforced by Lint is too small to
    // contain it.
    final int MAX_VALUE = 90;
    double npitch = Math.toRadians(Math.min(MAX_VALUE, Math.abs(pitch)));
    double nroll = Math.toRadians(Math.min(MAX_VALUE, Math.abs(roll)));
    return (float) (1.0 - Math.cos(npitch) * Math.cos(nroll));
  }

  // SensorListener implementation

  @Override
  public void onSensorChanged(SensorEvent sensorEvent) {
//    Log.d("OrientationSensor", "SensorEvent: " + sensorEvent.sensor.getName() + ":" + sensorEvent.toString());
    if (enabled) {
      final float[] values = sensorEvent.values;
      yaw = values[0];
      pitch = values[1];
      roll = values[2];
      accuracy = sensorEvent.accuracy;
//      Log.d("OrientationSensor", "yaw, pitch, roll: " + yaw + ", " + pitch + ", " + roll);
      OrientationChanged(yaw, pitch, roll);
    }
  }

  @Override
  public void onAccuracyChanged(Sensor sensor, int accuracy) {
    // TODO(user): Figure out if we actually need to do something here.
  }

  // Deleteable implementation

  @Override
  public void onDelete() {
    sensorManager.unregisterListener(this);
  }
}
