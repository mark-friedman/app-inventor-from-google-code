// Copyright 2009 Google Inc. All Rights Reserved.

package com.google.devtools.simple.runtime.components;

import com.google.devtools.simple.common.PropertyCategory;
import com.google.devtools.simple.runtime.annotations.DesignerProperty;
import com.google.devtools.simple.runtime.annotations.SimpleEvent;
import com.google.devtools.simple.runtime.annotations.SimpleFunction;
import com.google.devtools.simple.runtime.annotations.SimpleObject;
import com.google.devtools.simple.runtime.annotations.SimpleProperty;
import com.google.devtools.simple.runtime.components.util.BoundingBox;
import com.google.devtools.simple.runtime.errors.AssertionFailure;

/**
 * Device-independent abstract implementation of sprites.
 *
 * While the Simple programmer sees the x- and y-coordinates as integers,
 * they are maintained internally as doubles so fractional changes (caused
 * by multiplying the speed by a cosine or sine value) have the chance to
 * add up.
 *
 */
@SimpleObject
public abstract class SpriteComponent extends VisibleComponent implements AlarmHandler {
  protected int interval;      // number of milliseconds until next move
  protected boolean visible = true;
  // TODO(user): Convert to have co-ordinates be center, not upper left.
  // Note that this would simplify pointTowards to remove the adjustment
  // to the center points
  protected double xLeft;      // leftmost x-coordinate
  protected double yTop;       // uppermost y-coordinate
  protected float speed;       // magnitude in pixels

  /**
   * The angle, in degrees above the positive x-axis, specified by the user.
   * This is private in order to enforce that changing it also changes
   * {@link #heading}, {@link #headingRadians}, {@link #headingCos}, and
   * {@link #headingSin}.
   */
  private double userHeading;

  /**
   * The angle, in degrees <em>below</em> the positive x-axis, specified by the
   * user.  We use this to compute new coordinates because, on Android, the
   * y-coordinate increases "below" the x-axis.
   */
  private double heading;
  private double headingRadians;  // heading in radians
  private double headingCos;      // cosine(heading)
  private double headingSin;      // sine(heading)

  // Getters

  double getUserHeading() {
    return userHeading;
  }

  double getHeading() {
    return heading;
  }

  double getHeadingRadians() {
    return headingRadians;
  }

  double getHeadingCos() {
    return headingCos;
  }

  double getHeadingSin() {
    return headingSin;
  }

  // Methods for event handling

  /**
   * Requests a dispatch for the specified event.  The implementing class is
   * responsible for making sure that event handlers run with serial semantics,
   * e.g., appear atomic relative to each other.
   *
   * @param sprite the instance on which the event takes place
   * @param eventName the name of the event
   * @param args the arguments to the event handler
   */
  protected abstract void requestEvent(final SpriteComponent sprite,
                                       final String eventName,
                                       final Object... args);

  /**
   * Event handler called when the sprite reaches an edge of the screen.
   * If Bounce is then called with that edge, the sprite will appear to
   * bounce off of the edge it reached.
   */
  @SimpleEvent
  public void EdgeReached(int edge) {
    if (edge == Component.DIRECTION_NONE
        || edge < Component.DIRECTION_MIN
        || edge > Component.DIRECTION_MAX) {
      throw new IllegalArgumentException("Illegal argument " + edge +
          " to SpriteComponent.EdgeReached()");
    }
    requestEvent(this, "EdgeReached", edge);
  }

  /**
   * Handler for Touched events.
   *
   * @param x  x-coordinate of touched point
   * @param y  y-coordinate of touched point
   */
  @SimpleEvent
  public void Touched(float x, float y) {
    requestEvent(this, "Touched", x, y);
  }

  /**
   * Handler for Dragged events.  On all calls, the starting coordinates
   * are where the screen was first touched, and the "current" coordinates
   * describe the endpoint of the current line segment.  On the first call
   * within a given drag, the "previous" coordinates are the same as the
   * starting coordinates; subsequently, they are the "current" coordinates
   * from the prior call.  Note that the Sprite won't actually move
   * anywhere in response to the Dragged event unless MoveTo is
   * specifically called.
   *
   * @param startX the starting x-coordinate
   * @param startY the starting y-coordinate
   * @param prevX the previous x-coordinate (possibly equal to startX)
   * @param prevY the previous y-coordinate (possibly equal to startY)
   * @param currentX the current x-coordinate
   * @param currentY the current y-coordinate
   */
  @SimpleEvent
  public void Dragged(float startX, float startY,
                      float prevX, float prevY,
                      float currentX, float currentY) {
    requestEvent(this, "Dragged", startX, startY, prevX, prevY, currentX, currentY);
  }

  // Methods supporting properties related to AlarmHandler

  /**
   * Interval property getter method.
   *
   * @return  timer interval in ms
   */
  @SimpleProperty(
      description = "<p>The interval, in milliseconds, at which the sprite's " +
      "position is updated.  For example, if the speed is 10, the sprite will " +
      "move 10 pixels every interval.</p>",
      category = PropertyCategory.BEHAVIOR)
  public abstract int Interval();

  /**
   * Interval property setter method: sets the interval between timer events.
   *
   * @param interval  timer interval in ms
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_INTEGER,
      defaultValue = "1000")
  @SimpleProperty
  public abstract void Interval(int interval);

  /**
   * Enabled property getter method.
   *
   * @return  {@code true} indicates a running timer, {@code false} a stopped
   *          timer
   */
  @SimpleProperty(
      description = "Controls whether the sprite moves when its speed is non-zero.",
      category = PropertyCategory.BEHAVIOR)
  public abstract boolean Enabled();

  /**
   * Enabled property setter method: starts or stops the timer.
   *
   * @param enabled  {@code true} starts the timer, {@code false} stops it
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_BOOLEAN,
      defaultValue = "True")
  @SimpleProperty
  public abstract void Enabled(boolean enabled);

  // Methods supporting properties specific to SpriteComponent and its subclasses

  /**
   * Sets heading in which sprite should move.  In addition to changing the
   * local variables {@link #userHeading} and {@link #heading}, this
   * sets {@link #headingCos}, {@link #headingSin}, and {@link #headingRadians}.
   *
   * @param user_heading degrees above the positive x-axis
   */
  @SimpleProperty(
      category = PropertyCategory.BEHAVIOR)
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_FLOAT,
      defaultValue = "0")
  public void Heading(double user_heading) {
    userHeading = user_heading;
    // Flip, because y increases in the downward direction on Android canvases
    heading = -user_heading;
    headingRadians = Math.toRadians(heading);
    headingCos = Math.cos(headingRadians);
    headingSin = Math.sin(headingRadians);
    // changing the heading needs to force a redraw for image sprites that rotate
    registerChange();
  }

  /**
   * Returns the heading of the sprite.
   *
   * @return degrees above the positive x-axis
   */
  @SimpleProperty(
    description = "<p>Returns the sprite's heading in degrees above the positive " +
    "x-axis.  Zero degrees is toward the right of the screen; 90 degrees is toward the " +
    "top of the screen.</p>")
  public double Heading() {
    return userHeading;
  }

  /**
   * Turns this sprite to point towards a given other sprite.
   *
   * @param target the other sprite to point towards
   */
  @SimpleFunction(
    description = "<p>Turns the sprite to point towards a designated " +
    "target sprite. The new heading will be parallel to the line joining " +
    "the centerpoints of the two sprites.</p>")
  public void PointTowards(SpriteComponent target) {
    Heading(-Math.toDegrees(Math.atan2(
        // we adjust for the fact that the sprites' X() and Y()
        // are not the center points.
        target.Y() - Y() + (target.Height() - Height()) / 2,
        target.X() - X() + (target.Width() - Width()) / 2)));
  }

  /**
   * Sets the speed with which this sprite should move.
   *
   * @param speed the magnitude (in pixels) to move every {@link #interval}
   * milliseconds
   */
  @SimpleProperty(
      category = PropertyCategory.BEHAVIOR)
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_FLOAT,
      defaultValue = "0.0")
  public void Speed(float speed) {
    this.speed = speed;
  }

  /**
   * Gets the speed with which this sprite moves.
   *
   * @return the magnitude (in pixels) the sprite moves every {@link #interval}
   *         milliseconds.
   */
  @SimpleProperty(
    description = "<p>The speed at which the sprite moves.  The sprite moves " +
    "this many pixels every interval.</p>")
  public float Speed() {
    return speed;
  }

  // Methods supporting move-related functionality

  /**
   * Responds to a move or change of this sprite by checking for any
   * consequences (such as hitting the edge of the canvas), and notifying the
   * component that has responsibility for handling the change (e.g., the
   * containing canvas, which will redraw the sprite and check for collisions).
   *
   * The implementation here checks for hitting the edge of the canvas.
   * Subclasses should override this method to notify the containing canvas.
   */
  public void registerChange() {
    int edge = hitEdge();
    if (edge != Component.DIRECTION_NONE) {
      EdgeReached(edge);
    }
  }

  /**
   * Moves sprite directly to specified point.
   *
   * @param x the x-coordinate
   * @param y the y-coordinate
   */
  @SimpleFunction(
    description = "<p>Moves the sprite so that its left top corner is at " +
    "the specfied x and y coordinates.</p>")
  public void MoveTo(double x, double y) {
    xLeft = x;
    yTop = y;
    registerChange();
  }

  /**
   * Updates the x- and y-coordinates based on the heading and speed.  The
   * caller is responsible for calling {@link #registerChange()}.
   */
  protected void updateCoordinates() {
    xLeft += speed * headingCos;
    yTop += speed * headingSin;
  }

  // Methods for determining collisions and intersections

  protected final boolean overWestEdge() {
    return xLeft < 0;
  }

  protected final boolean overEastEdge(int canvasWidth) {
    return xLeft + Width() > canvasWidth;
  }

  protected final boolean overNorthEdge() {
    return yTop < 0;
  }

  protected final boolean overSouthEdge(int canvasHeight) {
    return yTop + Height() > canvasHeight;
  }

  /**
   * Specifies what edge of the canvas has been hit by the SpriteComponent, if
   * any, moving the sprite back in bounds.
   *
   * @return {@link Component#DIRECTION_NONE} if no edge has been hit, or a
   *         direction (e.g., {@link Component#DIRECTION_NORTHEAST}) if that
   *         edge of the canvas has been hit
   */
  protected abstract int hitEdge();

  protected final int hitEdge(int canvasWidth, int canvasHeight) {
    // Determine in which direction(s) we are out of bounds, if any.
    // Note that more than one boolean value can be true.  For example, if
    // the sprite is past the northwest boundary, north and west will be true.
    boolean west = overWestEdge();
    boolean north = overNorthEdge();
    boolean east = overEastEdge(canvasWidth);
    boolean south = overSouthEdge(canvasHeight);

    // If no edge was hit, return.
    if (!(north || south || east || west)) {
      return Component.DIRECTION_NONE;
    }

    // Move the sprite back into bounds.  Note that we don't just reverse the
    // last move, since that might have been multiple pixels, and we'd only need
    // to undo part of it.
    MoveIntoBounds();

    // Determine the appropriate return value.
    if (west) {
      if (north) {
        return Component.DIRECTION_NORTHWEST;
      } else if (south) {
        return Component.DIRECTION_SOUTHWEST;
      } else {
        return Component.DIRECTION_WEST;
      }
    }

    if (east) {
      if (north) {
        return Component.DIRECTION_NORTHEAST;
      } else if (south) {
        return Component.DIRECTION_SOUTHEAST;
      } else {
        return Component.DIRECTION_EAST;
      }
    }

    if (north) {
      return Component.DIRECTION_NORTH;
    }
    if (south) {
      return Component.DIRECTION_SOUTH;
    }

    throw new AssertionFailure("Unreachable code hit in SpriteComponent.hitEdge()");
  }

  /**
   * Provides the bounding box for this sprite.  Modifying the returned value
   * does not affect the sprite.
   *
   * @param border the number of pixels outside the sprite to include in the
   *        bounding box
   * @return the bounding box for this sprite
   */
  public BoundingBox getBoundingBox(int border) {
    return new BoundingBox(X() - border, Y() - border,
        X() + Width() - 1 + border, Y() + Height() - 1 + border);
  }

  /**
   * Determines whether two sprites are in collision.  Note that we cannot
   * merely see whether the rectangular regions around each intersect, since
   * some types of sprite, such as BallSprite, are not rectangular.
   *
   * @param sprite1 one sprite
   * @param sprite2 another sprite
   * @return {@code true} if they are in collision, {@code false} otherwise
   */
  public static boolean colliding(SpriteComponent sprite1, SpriteComponent sprite2) {
    // If the bounding boxes don't intersect, there can be no collision.
    BoundingBox rect1 = sprite1.getBoundingBox(1);
    BoundingBox rect2 = sprite2.getBoundingBox(1);
    if (!rect1.intersectDestructively(rect2)) {
      return false;
    }

    // If we get here, rect1 has been mutated to hold the intersection of the
    // two bounding boxes.  Now check every point in the intersection to see if
    // both sprites contain that point.
    // TODO(user): Handling abutting sprites properly
    for (double x = rect1.getLeft(); x <= rect1.getRight(); x++) {
      for (double y = rect1.getTop(); y <= rect1.getBottom(); y++) {
        if (sprite1.containsPoint(x, y) && sprite2.containsPoint(x, y)) {
          return true;
        }
      }
    }
    return false;
  }

  /**
   * Determines whether this sprite intersects with the given rectangle.
   *
   * @param rect the rectangle
   * @return {@code true} if they intersect, {@code false} otherwise
   */
  public boolean intersectsWith(BoundingBox rect) {
    // If the bounding boxes don't intersect, there can be no intersection.
    BoundingBox rect1 = getBoundingBox(0);
    if (!rect1.intersectDestructively(rect)) {
      return false;
    }

    // If we get here, rect1 has been mutated to hold the intersection of the
    // two bounding boxes.  Now check every point in the intersection to see if
    // the sprite contains it.
    for (double x = rect1.getLeft(); x < rect1.getRight(); x++) {
      for (double y = rect1.getTop(); y < rect1.getBottom(); y++) {
        if (containsPoint(x, y)) {
            return true;
        }
      }
    }
    return false;
  }

  /**
   * Indicates whether the specified point is contained by this sprite.
   * Subclasses of Sprite that are not rectangular should override this method.
   *
   * @param qx the x-coordinate
   * @param qy the y-coordinate
   * @return whether (qx, qy) falls within this sprite
   */
  public boolean containsPoint(double qx, double qy) {
    return qx >= xLeft && qx < xLeft + Width() &&
        qy >= yTop && qy < yTop + Height();
  }

  // Convenience methods for dealing with hitting the screen edge and collisions

  /**
   * Moves the sprite back in bounds if part of it extends out of bounds,
   * having no effect otherwise. If the sprite is too wide to fit on the
   * canvas, this aligns the left side of the sprite with the left side of the
   * canvas. If the sprite is too tall to fit on the canvas, this aligns the
   * top side of the sprite with the top side of the canvas.
   */
  @SimpleFunction
  public abstract void MoveIntoBounds();

  protected final void moveIntoBounds(int canvasWidth, int canvasHeight) {
    boolean moved = false;

    // We set the xLeft and/or yTop fields directly, instead of calling X(123) and Y(123), to avoid
    // having multiple calls to registerChange.

    // Check if the sprite is too wide to fit on the canvas.
    if (Width() > canvasWidth) {
      // Sprite is too wide to fit. If it isn't already at the left edge, move it there.
      // It is important not to set moved to true if xLeft is already 0. Doing so can cause a stack
      // overflow.
      if (xLeft != 0) {
        xLeft = 0;
        moved = true;
      }
    } else if (overWestEdge()) {
      xLeft = 0;
      moved = true;
    } else if (overEastEdge(canvasWidth)) {
      xLeft = canvasWidth - Width();
      moved = true;
    }

    // Check if the sprite is too tall to fit on the canvas. We don't want to cause a stack
    // overflow by moving the sprite to the top edge and then to the bottom edge, repeatedly.
    if (Height() > canvasHeight) {
      // Sprite is too tall to fit. If it isn't already at the top edge, move it there.
      // It is important not to set moved to true if yTop is already 0. Doing so can cause a stack
      // overflow.
      if (yTop != 0) {
        yTop = 0;
        moved = true;
      }
    } else if (overNorthEdge()) {
      yTop = 0;
      moved = true;
    } else if (overSouthEdge(canvasHeight)) {
      yTop = canvasHeight - Height();
      moved = true;
    }

    // Then, call registerChange (just once!) if necessary.
    if (moved) {
      registerChange();
    }
  }

  /**
   * Normalizes an angle to be in the range [0, 359).
   *
   * @param angle original value
   * @return equivalent angle in the range [0, 359).
   */
  private static double normalizeAngle(double angle) {
    angle = angle % 360;
    // The following step is necessary because Java's modulus operation yields a
    // negative number if the dividend is negative and the divisor is positive.
    if (angle < 0) {
      angle += 360;
    }
    return angle;
  }

  /**
   * Makes this sprite bounce, as if off of a wall by changing the
   * {@link #heading} (unless the sprite is not traveling toward the specified
   * direction).  This also calls {@link #MoveIntoBounds()} in case the
   * sprite is out of bounds.
   *
   * @param edge the direction of the object (real or imaginary) to bounce off
   *             of; this should be one of
   *    {@link com.google.devtools.simple.runtime.components.Component#DIRECTION_NORTH},
   *    {@link com.google.devtools.simple.runtime.components.Component#DIRECTION_NORTHEAST},
   *    {@link com.google.devtools.simple.runtime.components.Component#DIRECTION_EAST},
   *    {@link com.google.devtools.simple.runtime.components.Component#DIRECTION_SOUTHEAST},
   *    {@link com.google.devtools.simple.runtime.components.Component#DIRECTION_SOUTH},
   *    {@link com.google.devtools.simple.runtime.components.Component#DIRECTION_SOUTHWEST},
   *    {@link com.google.devtools.simple.runtime.components.Component#DIRECTION_WEST}, or
   *    {@link com.google.devtools.simple.runtime.components.Component#DIRECTION_NORTHWEST}.
   */
  @SimpleFunction(description = "<p>Makes this sprite bounce, as if off a wall.  " +
  "For normal bouncing, the edge argument should be the one returned by EdgeReached.</p>")
  public void Bounce(int edge) {
    MoveIntoBounds();

    // Normalize heading to [0, 360)
    double normalizedAngle = normalizeAngle(userHeading);

    // Only transform heading if sprite was moving in that direction.
    // This avoids oscillations.
    if ((edge == Component.DIRECTION_EAST
         && (normalizedAngle < 90 || normalizedAngle > 270))
        || (edge == Component.DIRECTION_WEST
            && (normalizedAngle > 90 && normalizedAngle < 270))) {
      Heading(180 - normalizedAngle);
    } else if ((edge == Component.DIRECTION_NORTH
                && normalizedAngle > 0 && normalizedAngle < 180)
               || (edge == Component.DIRECTION_SOUTH && normalizedAngle > 180)) {
      Heading(360 - normalizedAngle);
    } else if ((edge == Component.DIRECTION_NORTHEAST
                && normalizedAngle > 0 && normalizedAngle < 90)
              || (edge == Component.DIRECTION_NORTHWEST
                  && normalizedAngle > 90 && normalizedAngle < 180)
              || (edge == Component.DIRECTION_SOUTHWEST
                  && normalizedAngle > 180 && normalizedAngle < 270)
              || (edge == Component.DIRECTION_SOUTHEAST && normalizedAngle > 270)) {
      Heading(180 + normalizedAngle);
    }
  }

  // Sprite-specific properties

  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_FLOAT,
      defaultValue = "0.0")
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE)
  public void X(double x) {
    xLeft = x;
    registerChange();
  }

  @SimpleProperty(
      description = "<p>The horizontal coordinate of the left edge of the sprite, " +
      "increasing as the sprite moves to the right</p>.")
  public double X() {
    return xLeft;
  }

  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_FLOAT,
      defaultValue = "0.0")
  @SimpleProperty(
      category = PropertyCategory.APPEARANCE)
  public void Y(double y) {
    yTop = y;
    registerChange();
  }

  @SimpleProperty(
      description = "<p>The vertical coordinate of the top of the sprite, " +
      "increasing as the sprite moves down</p>.")
  public double Y() {
    return yTop;
  }

  /**
   * Gets whether sprite is visible.
   *
   * @return  {@code true} if the sprite is visible, {@code false} otherwise
   */
  @SimpleProperty(
      description = "<p>True if the sprite is visible.</p>",
      category = PropertyCategory.APPEARANCE)
  public boolean Visible() {
    return visible;
  }

  /**
   * Sets whether sprite should be visible.
   *
   * @param visible  {@code true} if the sprite should be visible; {@code false}
   * otherwise.
   */
  @DesignerProperty(editorType = DesignerProperty.PROPERTY_TYPE_BOOLEAN,
      defaultValue = "True")
  @SimpleProperty
  public void Visible(boolean visible) {
    this.visible = visible;
    registerChange();
  }
}
