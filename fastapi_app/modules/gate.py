import os
from typing import Annotated

from fastapi import APIRouter, Form, Path
from pydantic import BaseModel, Field

from fastapi_app.gpio_modules import Servo as GPIOServo
from fastapi_app.gpio_modules import ServoMoveRequest
from fastapi_app.utils import RunOnShutdown

GATE_CLOSE_ANGLE = int(os.getenv("GATE_CLOSE_ANGLE", -45))
GATE_OPEN_ANGLE = int(os.getenv("GATE_OPEN_ANGLE", 0))

GATE_1_ANGLE_OFFSET = float(os.getenv("GATE_1_ANGLE_OFFSET", 0))
GATE_2_ANGLE_OFFSET = float(os.getenv("GATE_2_ANGLE_OFFSET", 0))

gate_1 = GPIOServo(
    10,
    min_pulse_width=0.5475 / 1000,
    max_pulse_width=2.46 / 1000,
    angle_offset=GATE_1_ANGLE_OFFSET,
)
gate_1.schedule(ServoMoveRequest(GATE_CLOSE_ANGLE, 0), block=True)
RunOnShutdown.add(gate_1.close)


gate_2 = GPIOServo(
    9,
    min_pulse_width=0.555 / 1000,
    max_pulse_width=2.49 / 1000,
    angle_offset=GATE_2_ANGLE_OFFSET,
)
gate_2.schedule(ServoMoveRequest(GATE_CLOSE_ANGLE, 0), block=True)
RunOnShutdown.add(gate_2.close)


class GateFormData(BaseModel):
    angle: float = Field(
        description="Angle in degrees",
        examples=[-45, 0, 10, 45],
        ge=gate_1.min_angle,
        le=gate_1.max_angle,
    )
    duration: float = Field(
        description="Duration in seconds",
        examples=[0.5, 1.0],
        ge=0,
        le=2,
        default=0,
    )


router = APIRouter(
    prefix="/gate",
    tags=["gate (module MG90S)"],
)


# @router.get(
#     "/",
#     summary="Get gate state",
#     response_model=GateFormData,
# )
# def read_gate():
#     return GateFormData(state=gate.current_state)


@router.patch(
    "/{gate_id}",
    summary="Set gate state",
    response_model=GateFormData,
)
def set_gate(
    data: Annotated[GateFormData, Form()],
    gate_id: Annotated[int, Path(ge=1, le=2)],
):
    match gate_id:
        case 1:
            gate_1.schedule(
                ServoMoveRequest(data.angle, data.duration), block=False
            )
        case 2:
            gate_2.schedule(
                ServoMoveRequest(data.angle, data.duration), block=False
            )
        case _:
            raise ValueError(f"Invalid gate_id: {gate_id}")

    return data
