/* Mouse movement as the right stick and as the controller's gyro (Mac mouse mode, key 7: runtime/gamepad.m).
   The idea is yuzu's "mouse panning" (written anew here, no code taken): every movement adds to a held stick deflection;
   a tick every 10 ms (MOUSE_LOOK_TICK_NS) shows the deflection to the game and then lets it decay, so the camera keeps
   turning while the mouse moves and settles smoothly when it stops, whatever the mouse's report rate and the game's
   frame rate. The decay grows with the deflection (1 - length^2 * decay%), but is at least min_decay% a tick; the held
   length is cut to 1.5 (it may run past the stick's edge, which makes a steady turn easier to hold) and shown at most 1.
   A movement that leaves a deflection shorter than counterweight% is lifted to it, past the game's own stick dead zone.
   Units: one point of mouse movement (AppKit's deltaX / deltaY; deltaY grows downwards) moves the stick by
   sensitivity / 1000 of its range: at the default 50, 20 points is a full deflection.
   With TOTK_MOUSE_GYRO=1 (runtime/gamepad.m; off by default), the same movement also turns a controller lying face up (x right, y top edge, z out of the face: runtime/
   motion_fusion.c's frame): mouse right turns it clockwise seen from above (-z), mouse up tilts its top edge up (+x);
   per tick, sensitivity / 1000 * 2.5 revolutions a second per point, at most 2 revolutions a second. The gravity it
   reports follows the pitch (stopped at 80 degrees), so the sensor fusion keeps the aim where the mouse put it.
   Pacing (2026-10-28, user: the view jittered while Ultrahand held an object, where the aim camera reads the gyro): the
   window's moves come at the display's rate (AppKit coalesces them: 60-120 a second) and the tick every 10 ms, so a tick
   took one move, two or none, and a steady pan read as a gyro rate jumping between 0 and twice its speed (82 % spread at
   60 Hz). The stick's held deflection hid that; the gyro, which the game reads as it is, did not. So each move's turn
   is kept pending and the ticks release it at the mouse's own speed (movement / time between moves, averaged over about
   20 ms: mouse_look_move_at), corrected toward one move's worth still pending; the total turn is exactly the mouse's,
   a steady pan reads steady (6 % at 60 Hz, about 10 % at 90-144 Hz) and a stop ends one move later. A move more than
   50 ms after the last one, or without a time (mouse_look_move), is released at the next tick as before.
   Pointing (mouse_look_point; Tears of the Kingdom's ability wheel, which opens while L is held and picks the ability the
   right stick points at): the stick starts at the center and stays where the mouse puts it instead of settling back, its
   length cut to 1 so a turn of the mouse turns it at once, and the mouse turns neither the camera nor the gyro; when it
   ends the stick is centered again, so the camera does not turn on its own after the wheel closes.
   Plain C, no clock and no lock: the caller ticks it (gamepad.m, one timer while mouse mode is on) and serializes the
   calls; tests/mouse_look/probe.c covers it. */
#pragma once
#include <math.h>
#include <stdint.h>
#include <stdlib.h>

enum { MOUSE_LOOK_TICK_NS = 10000000 };
#define MOUSE_LOOK_MAX_LENGTH 1.5
#define MOUSE_LOOK_GYRO_GAIN 2.5        /* revolutions a second, per unit of stick movement in one tick */
#define MOUSE_LOOK_MAX_REV_S 2.0
#define MOUSE_LOOK_MAX_PITCH (80 * M_PI / 180)
#define MOUSE_LOOK_PACE_WINDOW 0.02     /* seconds the mouse's speed is averaged over */
#define MOUSE_LOOK_PACE_GAP 0.05        /* a longer pause between moves: the speed is unknown again */
#define MOUSE_LOOK_PACE_GAIN 0.1        /* per tick, of the pending turn beyond one move's worth */

typedef struct { int sensitivity, invert_y, counterweight, decay, min_decay; } MouseLookSettings;
typedef struct { double x, y; double pitch_move, yaw_move; double pitch; int pointing; double speed, reserve; uint64_t moved_ns; } MouseLook;   /* stick in units of its range; pitch_move / yaw_move: the turn pending; speed: units a second */

/* From the environment's text (NULL or out of range: the default). sensitivity 1-100 (50), invert_y 0/1 (0),
   counterweight / decay / min_decay 0-100 (20, 18, 6). */
static inline int mouse_look_setting(const char *text, int lo, int hi, int fallback) {
    if (!text || !*text) return fallback;
    char *end; long v = strtol(text, &end, 10);
    return *end || v < lo || v > hi ? fallback : (int)v;
}
static inline MouseLookSettings mouse_look_settings(const char *sensitivity, const char *invert_y, const char *counterweight,
                                                     const char *decay, const char *min_decay) {
    return (MouseLookSettings){
        .sensitivity = mouse_look_setting(sensitivity, 1, 100, 50), .invert_y = mouse_look_setting(invert_y, 0, 1, 0),
        .counterweight = mouse_look_setting(counterweight, 0, 100, 20), .decay = mouse_look_setting(decay, 0, 100, 18),
        .min_decay = mouse_look_setting(min_decay, 0, 100, 6)};
}

static inline void mouse_look_reset(MouseLook *m) { *m = (MouseLook){0}; }

/* Pointing on or off (the stick centered either way). */
static inline void mouse_look_point(MouseLook *m, int on) {
    if (!on == !m->pointing) return;
    m->pointing = on; m->x = m->y = 0; m->pitch_move = m->yaw_move = 0;
}

/* A move at now_ns (any monotonic clock; 0: no time, the turn goes out at the next tick). */
static inline void mouse_look_move_at(MouseLook *m, double dx, double dy, const MouseLookSettings *s, uint64_t now_ns) {
    if (!isfinite(dx) || !isfinite(dy)) return;
    const double kx = s->sensitivity / 1000.0, ky = s->invert_y ? -kx : kx;
    m->x += dx * kx; m->y += dy * ky;
    if (m->pointing) {
        const double length = hypot(m->x, m->y);
        if (length > 1) { m->x /= length; m->y /= length; }
        return;
    }
    m->yaw_move -= dx * kx; m->pitch_move -= dy * ky;
    if (!now_ns || !m->moved_ns) m->speed = 0;
    else if (now_ns > m->moved_ns) {   /* the same instant or out of order: the speed stays */
        const double dt = (now_ns - m->moved_ns) / 1e9, v = hypot(dx * kx, dy * ky) / dt, w = dt < MOUSE_LOOK_PACE_WINDOW ? dt / MOUSE_LOOK_PACE_WINDOW : 1;
        if (dt >= MOUSE_LOOK_PACE_GAP) m->speed = 0;
        else { m->speed = m->speed > 0 ? m->speed + (v - m->speed) * w : v; m->reserve = m->speed * dt; }
    }
    if (now_ns) m->moved_ns = now_ns;
    const double length = hypot(m->x, m->y), least = s->counterweight / 100.0;
    if (length > 0 && length < least) { m->x *= least / length; m->y *= least / length; }
}
static inline void mouse_look_move(MouseLook *m, double dx, double dy, const MouseLookSettings *s) { mouse_look_move_at(m, dx, dy, s, 0); }

/* One tick: the stick to show (rx, ry in -32767..32767, up positive), the gyro in rad/s and the gravity in G for this
   tick (a controller lying face up reads z = -1 G); then the held deflection decays. */
static inline void mouse_look_tick(MouseLook *m, const MouseLookSettings *s, int32_t *rx, int32_t *ry, double gyro[3], double acc[3]) {
    double length = hypot(m->x, m->y);
    if (length > MOUSE_LOOK_MAX_LENGTH) { m->x *= MOUSE_LOOK_MAX_LENGTH / length; m->y *= MOUSE_LOOK_MAX_LENGTH / length; length = MOUSE_LOOK_MAX_LENGTH; }
    double ox = m->x, oy = -m->y, shown = hypot(ox, oy);
    if (shown > 1) { ox /= shown; oy /= shown; }
    *rx = (int32_t)lround(ox * 32767); *ry = (int32_t)lround(oy * 32767);
    if (m->pointing) {   /* held where the mouse put it; no turn */
        gyro[0] = gyro[1] = gyro[2] = 0;
        acc[0] = 0; acc[1] = -sin(m->pitch); acc[2] = -cos(m->pitch);
        return;
    }
    const double c = length < 1 ? length : 1, decay = 1 - c * c * s->decay / 100.0, most = 1 - s->min_decay / 100.0;
    const double keep = decay < most ? decay : most;
    m->x *= keep > 0 ? keep : 0; m->y *= keep > 0 ? keep : 0;
    if (fabs(m->x) < 1e-6 && fabs(m->y) < 1e-6) m->x = m->y = 0;

    double pm = m->pitch_move, ym = m->yaw_move, pending = hypot(pm, ym);
    if (pending > 0 && m->speed > 0) {   /* paced: the mouse's speed, corrected toward one move's worth pending */
        double out = m->speed * (MOUSE_LOOK_TICK_NS / 1e9) + MOUSE_LOOK_PACE_GAIN * (pending - m->reserve);
        if (out < 0) out = 0;
        if (out < pending) { pm *= out / pending; ym *= out / pending; }
    }
    m->pitch_move -= pm; m->yaw_move -= ym;
    if (fabs(m->pitch_move) < 1e-12 && fabs(m->yaw_move) < 1e-12) m->pitch_move = m->yaw_move = 0;
    double pitch = pm * MOUSE_LOOK_GYRO_GAIN, yaw = ym * MOUSE_LOOK_GYRO_GAIN, rate = hypot(pitch, yaw);
    if (rate > MOUSE_LOOK_MAX_REV_S) { pitch *= MOUSE_LOOK_MAX_REV_S / rate; yaw *= MOUSE_LOOK_MAX_REV_S / rate; }
    gyro[0] = pitch * 2 * M_PI; gyro[1] = 0; gyro[2] = yaw * 2 * M_PI;
    m->pitch += gyro[0] * (MOUSE_LOOK_TICK_NS / 1e9);
    if (m->pitch > MOUSE_LOOK_MAX_PITCH) m->pitch = MOUSE_LOOK_MAX_PITCH;
    if (m->pitch < -MOUSE_LOOK_MAX_PITCH) m->pitch = -MOUSE_LOOK_MAX_PITCH;
    acc[0] = 0; acc[1] = -sin(m->pitch); acc[2] = -cos(m->pitch);
}
