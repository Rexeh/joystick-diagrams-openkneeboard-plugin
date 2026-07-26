# Joystick Diagrams — OpenKneeboard Plugin

Output plugin for [Joystick Diagrams](https://github.com/Rexeh/joystick-diagrams) that copies
exported PNG diagrams into the OpenKneeboard content directories so they appear automatically
in-cockpit without manual file management.

This plugin is **not bundled** with the application. Install it from inside Joystick Diagrams via
**Plugins → Store**, or point the installer at a release ZIP below.

- **Plugin ID:** `1f1ce378-f17c-42fa-ab3e-7b1fc4cf2989`
- **Type:** output
- **Current version:** 1.0.0

## Repository layout

```
openkneeboard/        # the importable plugin package — this folder is what ships in the release ZIP
  __init__.py
  main.py             # OutputPlugin entry point + OpenKneeboardSettings
  aircraft_map.py     # built-in profile-name → DCS module folder mapping
  img/openkneeboard.ico
tests/                # standalone tests (pytest tmp_path, no data fixtures)
scripts/sign_plugin.py
```

## How it loads in the host

At runtime the host app imports this package and resolves `joystick_diagrams.*` against itself, so
imports of `joystick_diagrams.input.*`, `...output_plugin_interface`, and `...plugin_settings` stay
**absolute**. Intra-plugin imports (e.g. `from .aircraft_map import KNOWN_DCS_AIRCRAFT`) are
**relative**.

Installed plugins cannot ship their own PyPI dependencies — they run inside the host's frozen
environment. This plugin needs no third-party runtime packages beyond the host SDK.

## Development

```bash
# Install the host package (provides the joystick_diagrams SDK) plus dev tooling
pip install "joystick-diagrams @ git+https://github.com/Rexeh/joystick-diagrams@master"
pip install -e ".[dev]"

pytest tests/
ruff check .
```

## Releasing

Tag a release as `vX.Y.Z` (matching `plugin_meta.version` in `main.py`). The release workflow
zips the `openkneeboard/` folder, optionally signs it (see below), computes its SHA-256, and
publishes `openkneeboard.zip` as a release asset.

Then update the catalog manifest entry (`download_url` + `sha256`) that the app reads.

### Signing (for first-party "verified" releases)

The store shows this plugin as **Verified** only if the release ZIP contains a valid `plugin.sig`.
Signing uses the project's Ed25519 developer **private** key, stored as the repository/organisation
Actions secret `PLUGIN_SIGNING_KEY` (PEM). The matching public key is baked into the host
(`joystick_diagrams/plugins/plugin_signing.py`). Without the secret the workflow still ships an
**unsigned** ZIP (installs with a trust prompt).
