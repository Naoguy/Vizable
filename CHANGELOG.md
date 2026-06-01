# Vizable — Changelog

---

## v0.1.0 — 2026-06-01

First release. Camera and Lights panels are fully built to v1 scope.

### Camera panel
- List all cameras in the scene; click to set as active
- Per-camera controls: focal length, sensor width, clip start/end
- Aspect ratio presets (16:9, 4:3, 3:2, 1:1, 9:16, 3:4) — updates the
  render resolution live so the viewport frame reflects the choice
- Depth of field: click-to-place focus empty, f-stop, clear
- Tracking: click-to-place track target empty, toggle on/off, retarget, remove
- Save current viewport angle as a new camera
- Rename and delete cameras from the panel
- New cameras auto-placed in a **Vizable Cameras** collection

### Lights panel
- List all lights; click to expand controls
- Quick-add: Area, Point, Spot, Sun with sensible defaults per type
- Per-light: strength, type-aware size/softness (radius, cone, angle)
- Colour temperature: Kelvin slider (1 000–10 000 K) drives lamp colour;
  toggle back to raw colour picker at any time
- Spherical positioning: set elevation, azimuth, and distance around a
  nominated subject object
- Tracking: same click-to-place empty mechanism as cameras
- Rename and delete lights from the panel
- New lights auto-placed in a **Vizable Lights** collection
- Scene subject picker (used as the orbit centre for spherical positioning)

### Cross-cutting
- Removing tracking or DOF bakes the current look direction into the object
  so it holds its orientation rather than snapping back
- Removing tracking or DOF also deletes the associated target empty — no
  orphaned objects left in the scene
- Retargeting reuses the existing empty (moves it) rather than creating a
  new one each time
