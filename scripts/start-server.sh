#!/bin/bash

set -e

export GATE_OPEN_ANGLE=90
export GATE_CLOSE_ANGLE=180
export GATE_ANGLE_OFFSET=0.3

fastapi run fastapi_app/main.py --port 8000