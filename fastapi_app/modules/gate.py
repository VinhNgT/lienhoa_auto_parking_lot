import atexit
import os
from contextlib import asynccontextmanager
from enum import Enum
from typing import Annotated, Final

from fastapi import APIRouter, Form
from pydantic import BaseModel, Field

from fastapi_app.gpio_modules import ServoHwPwm
from fastapi_app.utils.request_queue import RequestQueue


class GateState(str, Enum):
    OPEN = "open"
    CLOSE = "close"


class Gate:
    OPEN_ANGLE: Final = int(os.getenv("GATE_OPEN_ANGLE", 90))
    CLOSE_ANGLE: Final = int(os.getenv("GATE_CLOSE_ANGLE", 180))
    GATE_ANGLE_OFFSET: Final = float(os.getenv("GATE_ANGLE_OFFSET", 0.3))

    def __init__(self):
        print(
            f"Gate: OPEN_ANGLE={self.OPEN_ANGLE}, "
            f"CLOSE_ANGLE={self.CLOSE_ANGLE}, "
            f"GATE_ANGLE_OFFSET={self.GATE_ANGLE_OFFSET}"
        )

        self._servo = ServoHwPwm(
            pwm_channel=0,
            initial_angle=self.CLOSE_ANGLE,
            angle_offset=self.GATE_ANGLE_OFFSET,
        )

        self.set_status(GateState.CLOSE)
        atexit.register(self._servo._cleanup)

    def set_status(self, state: GateState):
        match state:
            case GateState.CLOSE:
                self._servo.ease_angle(self.CLOSE_ANGLE, ease_seconds=0.5)

            case GateState.OPEN:
                self._servo.ease_angle(self.OPEN_ANGLE, ease_seconds=0.5)

        self.current_state = state


class GateStateResponse(BaseModel):
    state: GateState = Field(
        description="Current state of the gate",
        examples=["open", "close"],
    )


gate = Gate()
request_queue = RequestQueue(3)


@asynccontextmanager
async def lifespan(app: APIRouter):
    yield
    request_queue.shutdown()


router = APIRouter(
    prefix="/gate",
    tags=["gate (module MG90S)"],
    lifespan=lifespan,
)


@router.get(
    "/",
    summary="Get gate state",
    response_model=GateStateResponse,
)
def read_gate():
    return GateStateResponse(state=gate.current_state)


@router.patch(
    "/",
    summary="Set gate state",
    response_model=GateStateResponse,
)
def set_gate(state: Annotated[GateState, Form()]):
    request_queue.submit(gate.set_status, state)

    return GateStateResponse(state=gate.current_state)
