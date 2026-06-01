# Vizable — Foundation Brief

*Blender addon for KeyShot-style product visualisation*
*Starting context for Claude Code build. Updated draft.*

---

## 1. What Vizable is

Vizable is a Blender addon that brings a KeyShot-style scene control and rendering workflow to Blender, aimed at product visualisation. It surfaces the things a product designer touches most often (cameras, lights, render setup) in simple, parameter-driven panels, so a designer coming from KeyShot can work without having to think in Blender's object-and-datablock model.

It is built first for the Morrama team migrating from KeyShot, but it is designed clean, standalone, and open-ended from day one. Nothing in the build should tie it to Morrama-specific infrastructure or otherwise close off where it could go later.

**It is not** a fork, a stripped-down Blender, or a replacement for the native UI. Full Blender stays fully accessible underneath. Vizable is an additive convenience layer.

---

## 2. Core design principles

Every decision is checked against these.

1. **Reduce decisions, not add them.** The target user is a product designer, not a Blender technical artist. A panel that exposes forty options has failed. Expose what matters, hide the rest, pick good defaults.
2. **Detect the scene, do not own it.** Panels read the current scene and act on whatever they find. Vizable does not require a specific asset library path, file structure, or assets loaded a particular way. If a light or material was added by any route, it shows up in the panel because it is in the scene. This keeps the addon portable and stops it becoming brittle as the team or its file structure grows.
3. **Stay open-ended.** Build clean and self-contained so no path is closed off. We do not write anything that depends on a particular file, a particular library, or a particular deployment.
4. **Predictable beats clever.** Where there is a choice between elegant-but-fragile and plain-but-robust, prefer robust. The team cannot debug clever.

---

## 3. The KeyShot mental model we are translating

KeyShot users expect:

- A **camera** concept where you save viewpoints, switch between them, lock them, aim them, and adjust lens and depth of field in one place. In Blender, cameras are scene objects, which feels indirect.
- An **environment and lighting** model that is parameter-led (rotate the HDRI, position a light by feel, aim it at a point) rather than object-transform-led.
- A **render** step with a queue, resolution and aspect handling, and the ability to fire off several outputs without babysitting each one.

Vizable's three panels map onto these three expectations.

---

## 4. Architecture (settled)

- **Single addon, tabbed panels.** One addon called **Vizable**, presenting sub-panels grouped under a single tab. Install one thing once; the feature surface grows under the team as panels are added.
- **Location: the N-panel.** Panels live in the 3D viewport sidebar (the panel opened with `N`), under a dedicated Vizable tab.
- **Surface beyond the panel.** Quick actions (e.g. add selected to a collection, drop a target empty, toggle tracking) are also exposed through a **pie menu and/or shortcuts**, not only the panel. The panel is the home; the pie menu and shortcuts are the fast path.
- **Packaging: as an Extension.** Built as a Blender extension (the 4.2+ standard): manifest-based, installed by drag-and-drop, updated cleanly. Not a legacy addon.
- **Minimum Blender version: 5.1.** Code targets 5.1 and up. We do not carry compatibility shims for older versions.

Note on maintenance: Blender's release pace is fast (5.0 Nov 2025, 5.1 March 2026, 5.2 and 5.3 expected later in 2026) and point releases can change the Python API. Targeting 5.1+ cleanly is the simplest position and the right one for the team.

---

## 5. Cross-cutting concepts

These behaviours span more than one panel, so they are defined once here and referenced by the panels below.

### Empties as targets (tracking and focus)

Both tracking and depth of field aim at a **point in space via an empty**, never directly at an object.

- **Why not the object.** Aiming or focusing at an object uses its origin. For a large product the origin is often off-centre or nowhere near the visual centre, so the result is unpredictable and you cannot choose where on or in the object the aim/focal point sits.
- **The empty solves both.** An empty gives a precise, movable target you can place exactly where you want the camera or light pointed, or exactly where the focal plane should fall (including a point inside the object).

### Viewport interaction layer

Over time Vizable combines viewport-based controls for dynamic, intuitive setup rather than typing values. This is the layer that makes it feel like KeyShot. It includes, progressively:

- **Click-to-place empties** in the viewport for tracking targets and DOF focus points. This is the first and most important piece, since tracking and DOF both depend on it.
- Aiming **light direction** and **camera direction** by interacting in the viewport.
- Setting a **highlight** by clicking where on the product you want a light's highlight or reflection to land.
- Control **gizmos** for the above where they help.

Click-to-place empties are in scope early because tracking and DOF need them. The richer aiming and highlight controls grow from the same mechanism afterwards.

### Collection organisation

Vizable helps keep scenes tidy by organising its objects into collections.

- Cameras and lights created or managed through Vizable can be placed into dedicated collections by default.
- Adding selected cameras/lights to a collection is available from the panel, the pie menu, and a shortcut.
- This keeps the outliner readable and underpins later work (a saved lighting setup is naturally a collection, see Lights > Later).

---

## 6. The three panels

Scoped as **v1** (build now) versus **Later** (deliberately deferred to keep v1 shippable and trustworthy).

### Panel 1 — Cameras *(build first)*

The quickest win and lowest-risk panel, because it mostly surfaces camera data Blender already exposes. Building it first establishes the panel structure, the empties mechanism, and the install/reload loop reused everywhere else.

**v1**
- List all cameras in the scene, click to set active.
- Per-camera controls in one place: focal length, sensor size, clip start/end.
- **Aspect ratio per camera, with templates.** Aspect (and therefore orientation: landscape, portrait, square, or a set ratio) is a property of the camera. Provide sensible aspect templates. See the resolution/aspect relationship under the Render panel.
- **Depth of field via an empty.** DOF focus targets a click-to-placed empty, not an object, so the exact focal point is controllable (see Cross-cutting > Empties). Expose toggle, focus empty, f-stop.
- **Tracking via an empty, toggleable.** A toggle that aims the camera at a click-to-placed empty using a Track To constraint (see Cross-cutting > Empties).
- "Save current view as camera" — create a camera from the current viewport angle.
- Add cameras to a Vizable cameras collection by default; rename/delete from the panel.

**Later**
- Turntable setup (camera or object rotation for a spin render).
- Standard view presets (front, three-quarter, top) as one-click placements.
- Richer viewport aiming and gizmos (see Cross-cutting > Viewport interaction layer).

### Panel 2 — Lights *(build second)*

Parameter-driven control of lighting so a designer positions and tunes lights by feel rather than by grabbing and rotating objects.

**Build decision, settled: do not base this on geometry-nodes light instancing.** Instancing real lights through geometry nodes is fragile (lights can vanish during unrelated node operations, emission behaviour is inconsistent across object-info versus collection-info, and it tends to break across versions) and unfit for a beginner-facing tool because nobody could debug it. Instead, drive **real light objects** through a normal Python panel, using drivers or a simple empty-based rig where helpful. Same parametric feel, far more robust, survives version bumps. Reserve geometry nodes for genuinely procedural lighting later.

**v1**
- Detect all lights in the scene and list them.
- Per-light parametric controls: strength/power, colour temperature (Kelvin) as well as raw colour, size/softness.
- Positioning by parameter: elevation (height angle), azimuth (orbit angle around the subject), distance. The KeyShot-style "move the light around the object by feel" control.
- **Tracking via an empty, toggleable.** Same mechanism as cameras: aim a light at a click-to-placed empty (see Cross-cutting > Empties).
- Quick add of common light types with sensible defaults.
- Add lights to a Vizable lighting collection by default.

**Later**
- Load saved studio lighting setups in one click. Because of the detect-the-scene principle, lights brought in from a library simply appear and become controllable. One-click "swap lighting environment."
- HDRI / environment control: rotation, strength, swap, from a single panel control.
- Highlight placement and richer viewport aiming (see Cross-cutting > Viewport interaction layer).
- Genuinely procedural lighting (arrays, repeated fixtures) where geometry nodes earns its complexity.

**Saving a lighting setup to the library (Later, needs design)**
A good lighting setup is worth saving for reuse, naturally as a collection. The hard requirement: the saved setup must **not depend on the file it was created in**. It should migrate cleanly into library files set up to hold it, so it can be pulled into any future project. How exactly this packaging and migration works is to be designed when we reach it; flag it now so the lighting data is kept self-contained from the start.

### Panel 3 — Studio / Batch Render *(build last)*

The biggest KeyShot pain point and the highest-value panel, but the hardest, with the longest tail of edge cases. The risk is not writing version one; it is that version one works in the demo and breaks on the untested combination before a deadline. Build the simplest reliable core first.

**Resolution and aspect: linked but separate, the same way Blender's own properties separate them.**
- **Aspect is a camera decision** (Camera panel, with templates). It defines orientation and proportions.
- **Resolution is a render decision** (this panel, with templates/defaults). It defines pixel budget and quality.
- **Vizable resolves the two intelligently at render time.** A resolution preset describes a pixel budget rather than a fixed width and height. The active camera's orientation decides how that budget maps to width versus height. Example: a portrait camera with a 1920x1080 resolution preset renders 1080x1920. So the same resolution preset produces correct dimensions whether the camera is landscape, portrait, or square. Once this is in place we will see whether the template sets for each feel right and adjust.

**v1 (dumb but reliable)**
- A render queue: a list of jobs, each job = a camera + a resolution preset + an output name.
- Resolution presets/templates; aspect comes from each job's camera (above).
- Render the queue in sequence, each output written to a clearly named file.
- Output naming system so files do not collide or confuse.

**Later (full studio state system, revisited deliberately)**
The full "studio state" capture (visibility sets, active lighting setup, camera, resolution, aspect, and CMF/material variants, batched across the full matrix) carries a lot to consider and is deferred. We circle back to design it once the reliable render core exists and is trusted. Noted here so the v1 core is built without painting us into a corner.

---

## 7. Build order and rationale

1. **Cameras.** Fast working v1, builds team trust early, and establishes the panel structure, the empties/click-to-place mechanism, and the install/reload loop reused everywhere else.
2. **Lights.** Higher complexity but well-bounded if we avoid the geo-nodes trap. Big perceived value for KeyShot refugees, and it reuses the empties and collection mechanisms from the camera panel.
3. **Render queue.** Highest value, highest risk. Build the reliable core, ship it, then design the full studio-state system once the core is trusted.

Do not start a panel until the previous one is genuinely working in the team's hands. Resist building all three half-way.

---

## 8. Deferred scope (on the record, intentionally not now)

- **Full studio-state capture** (render panel). Visibility, lighting, camera, resolution, aspect, and CMF variants captured and replayed, batched across combinations. Revisited after the v1 render core exists.
- **Commercial path.** Not a consideration now. The only requirement it places on the build today is the one we are already following: keep everything clean, self-contained, and open-ended so nothing limits where Vizable can go.

---

## 9. Build environment notes

- Vizable is a multi-file Python project and is built in **Claude Code** (or Cowork), not authored through chat. This brief is the project's starting context.
- The **Blender connector** must be configured in the build environment. The development loop is: write, install, reload, check the UI did not throw, adjust. Without live Blender access that loop is blind, so confirm the connector is wired up before starting.
- Package and test as a **5.1+ extension** from the start.

---

*Vizable — Foundation Brief. Living context for the Claude Code build; expected to evolve as panels are built.*
