# Vizable — Roadmap & Open Tasks

> **Why this file exists:** Claude's task list and chat history are stored
> locally per machine and do **not** sync through git. This file is the durable,
> cross-machine record of outstanding work. Update it as things change.

_Last updated: 2026-06 (after suite restructure + STEP Importer v1.4.0)._

---

## STEP Importer

### Cleanup (small, do when convenient)
- Rename internal identifiers from the `morrama` namespace to `vizable` for
  brand consistency: operator `morrama.import_step` → `vizable.import_step`,
  classes `MORRAMA_OT_ImportStep` / `MORRAMA_PT_import_panel` →
  `VIZABLE_*`, and the report string prefix. **Not user-visible** (the N-panel
  tab is already `"Vizable"`), purely internal tidiness. Update the panel's
  `operator(...)` call to match if the idname changes.

### v2 — full-fidelity converter (the big one)
- **Goal:** preserve deeply nested assembly hierarchy and keep every body
  separate with its real name — fixes both current limitations at once.
- **Approach:** read STEP directly via OpenCASCADE's XCAF model (assembly tree,
  names, colours, units) instead of the lossy STEP→GLB step. Reuse the ~36 MB
  OCCT engine already bundled in `extensions/step_importer/bin/` via a small
  custom converter that walks XCAF and emits nested structure.
- **Blocker:** Windows **Smart App Control** blocks unsigned native binaries
  (in-process and subprocess; install method is irrelevant). The bundled
  `step2glb` passes only via accrued cloud reputation.
- **Unlock:** Authenticode **code-signing** every native file with an RSA cert
  from a Microsoft-trusted CA (e.g. **Microsoft Trusted Signing**, ~$10/mo).
  With timestamping, signed binaries stay valid after the cert lapses, so the
  cost is effectively per-release, not ongoing.
- **Open decision:** does the team want to set up code-signing? That single
  choice gates this entire path.

### Known v1 limitations (from the bundled step2glb converter)
- Deeply nested sub-assemblies flatten to a single level.
- Multiple bodies inside one sub-assembly may merge into one mesh.
- Plasticity exports carry no part names, so those parts import unnamed.

---

## Vizable (visualisation addon)

Per `Vizable_Foundation_Brief.md`, build order is **Cameras → Lights → Render
queue**. See the brief for the full scope and the deliberately-deferred items
(full studio-state capture, HDRI control, viewport aiming/gizmos, saved lighting
setups).

---

## Suite / infrastructure

- **More tools (future):** graphics, render management, and other designer
  utilities — each added as a new folder under `extensions/`. `build.bat`
  auto-discovers and builds them; they appear in the same repo index.
- **Shared code:** when a second tool needs shared helpers, add a `core/`
  library and vendor it into each extension at build time (Blender has no
  inter-extension dependency mechanism — extensions must be self-contained).
- **Distribution:** currently a self-hosted extension repository served from
  `docs/` via GitHub Pages (`https://naoguy.github.io/Vizable/index.json`).
  Could add GitHub Releases later if useful.

---

## Notes for picking up on another machine

- `git clone https://github.com/Naoguy/Vizable.git` brings all code + binaries.
- Set the Blender path at the top of `build.bat` to match that machine.
- The standalone STEP-importer repo at `C:\Dev\STEP Importer` (this dev machine
  only, never pushed) is redundant now — kept as a local backup for now.
