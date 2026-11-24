# Changelog

Each release has a section; its text becomes the GitHub release notes and the Marketplace's
"what's new". New entries are fragments in `changelog.d/`: `python scripts/changelog.py collect`
adds them under `## [Unreleased]`, and `mason bump` turns that into the version.

## 1.0.2

- Shows its own icon in Floorbit's plugin list and Marketplace.

## 1.0.1

- Keeps reading for the whole event when a round goes wrong. A meter that answers NaN, a list or
  something that isn't JSON, or something that isn't a web server at a meter's address, used to stop
  the reading until the agent restarted; now that meter shows as failing and the others are read.
- A reading of NaN, infinity or `true` is no reading, and channel `-1` is refused.

## 1.0.0

- First release from its own repository. Until now the plugin shipped inside Floorbit; it works
  the same, and the local agents get it as the same signed file.
