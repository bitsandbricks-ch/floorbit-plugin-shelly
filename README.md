# Shelly power meters for Floorbit

[![Test and release](https://github.com/bitsandbricks-ch/floorbit-plugin-shelly/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/bitsandbricks-ch/floorbit-plugin-shelly/actions/workflows/release.yml?query=branch%3Amain)

The `shelly` plugin for [Floorbit](https://github.com/bitsandbricks-ch/floorbit). Install it under
Settings > Plugins > Marketplace; what it does and how to set it up is in Floorbit's
[docs/power.md](https://github.com/bitsandbricks-ch/floorbit/blob/master/docs/power.md).

## What is where

| File | What |
| --- | --- |
| `plugin.yaml` | The manifest: settings, what it may touch, what the agent part sends. |
| `plugin.py` | The part that runs in Floorbit. |
| `agent.py` | The part that runs on the local agent in the hall. |
| `tests/` | Tests, against Floorbit at the commit in `FLOORBIT_REF`. No network but localhost. |

## Testing

```
git clone https://github.com/bitsandbricks-ch/floorbit ../floorbit
git -C ../floorbit checkout "$(cat FLOORBIT_REF)"
pip install -r ../floorbit/requirements.txt pytest ruff
ruff check --config ../floorbit/pyproject.toml --config 'lint.isort.known-third-party=["floorbit"]' .
PYTHONPATH=../floorbit python -m pytest -q tests
```

## Releasing

Put the new version into `plugin.yaml`, add a `## <version>` section to `CHANGELOG.md`, merge, then
push the tag:

```
git tag v1.0.1 && git push origin v1.0.1
```

The [workflow](.github/workflows/release.yml) tests it, signs `shelly-<version>.tar.gz` with the
Floorbit plugin key (environment `plugin-signing`, secret `FLOORBIT_PLUGIN_SIGNING_KEY`) and
attaches it to the GitHub release. The Marketplace picks it up within the hour. A version is
withdrawn in [floorbit-plugins](https://github.com/bitsandbricks-ch/floorbit-plugins)' `plugins.yaml`,
never by deleting the release.
