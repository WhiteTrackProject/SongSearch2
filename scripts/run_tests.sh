#!/usr/bin/env bash
set -euo pipefail

export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-offscreen}
export PYTEST_DISABLE_PLUGIN_AUTOLOAD=1

python scripts/verify_environment.py
coverage run -m pytest "$@"
coverage report -m
python scripts/smoke_app.py
