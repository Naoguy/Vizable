# Vizable

A suite of Blender tools for industrial / product designers — a growing
workflow layer covering CAD import, KeyShot-style visualisation, and render
management. Each tool is a self-contained Blender 5.1+ extension; install only
the ones you want, or the whole suite.

## Tools

| Tool | ID | What it does |
|------|----|--------------|
| **Vizable** | `vizable` | KeyShot-style cameras, lights and render queue, in simple N-panel sub-panels. |
| **Vizable: STEP Importer** | `vizable_step_importer` | Imports STEP/STP CAD files with real part names, a file-named collection, a root empty at the model base, and unit/scale handling. |

All tools share the **Vizable** N-panel tab in the 3D viewport (press `N`).

## Installing (for the team)

The suite is published as a **Blender extension repository**, so you add one
URL once and then install/update any tool from inside Blender:

1. **Edit › Preferences › Get Extensions › Repositories (▾) › Add Remote
   Repository**, and enter the suite repo URL:
   `https://naoguy.github.io/Vizable/index.json`
2. Back in **Get Extensions**, the Vizable tools appear. Install whichever you
   want. Updates are delivered through the same repo automatically.

(You can also install any tool's zip manually via **Install from Disk** using
the zips under `docs/`.)

## Repository layout

```
extensions/
  vizable/              ← visualisation addon (cameras / lights / render)
  step_importer/        ← STEP/STP CAD importer (bundles step2glb + OpenCASCADE)
docs/                   ← published extension repository (GitHub Pages)
  index.json            ← the repo index Blender reads
  *.zip                 ← built extension packages
build.bat               ← builds every extension into docs/ and regenerates the index
Vizable_Foundation_Brief.md
CHANGELOG.md
```

## Building / releasing

Requires Blender 5.1+ (path set at the top of `build.bat`):

```
build.bat
```

This builds every extension under `extensions/` into `docs/`, regenerates
`docs/index.json`, then you commit and push `docs/` to deploy via GitHub Pages.
Each extension versions independently via its own `blender_manifest.toml`.

## Adding a new tool to the suite

1. Create `extensions/<your_tool>/` with its own `blender_manifest.toml`
   (unique `id`) and `__init__.py`.
2. Use `bl_category = "Vizable"` on its panels to share the suite tab.
3. Run `build.bat` — it auto-discovers and builds every extension folder.

## Notes

- **STEP importer limitations (v1):** deeply nested sub-assemblies flatten;
  multiple bodies in one sub-assembly may merge; Plasticity exports carry no
  part names. These stem from the bundled `step2glb` converter. Full-fidelity
  nested hierarchy is a future direction gated on code-signing (Windows Smart
  App Control blocks unsigned OpenCASCADE Python bindings).
- `step2glb` + bundled OpenCASCADE libraries are redistributed from the
  Step2Blend project (Louis Rist, mrrist.com) under its license.
