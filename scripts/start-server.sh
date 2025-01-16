#!/bin/bash

set -e

# export GATE_CLOSE_ANGLE=-45
# export GATE_OPEN_ANGLE=0
export GATE_1_ANGLE_OFFSET=0
export GATE_2_ANGLE_OFFSET=0

export IS_DOCKER=FALSE

fastapi run fastapi_app/main.py --port 8000