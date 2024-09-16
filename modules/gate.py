from enum import Enum
from pydantic import BaseModel
from fastapi import APIRouter, Form, BackgroundTasks
from typing import Annotated
from gpio_modules.servo_hw_pwm import ServoHwPwm
import atexit
import threading


class GateState(str, Enum):
    OPEN = "open"
    CLOSE = "close"


class Gate:
    def __init__(self):
        self._servo = ServoHwPwm(pwm_channel=0)
        self._lock = threading.Lock()

        self.set_status(GateState.CLOSE)
        atexit.register(self._servo.cleanup)

    def set_status(self, state: GateState):
        with self._lock:
            match state:
                case GateState.CLOSE:
                    self._servo.ease_angle(0, ease_seconds=0.5)

                case GateState.OPEN:
                    self._servo.ease_angle(90, ease_seconds=0.5)

            self.current_state = state


class GateStateResponse(BaseModel):
    state: GateState


router = APIRouter(
    prefix="/gate",
    tags=["gate"],
)
gate = Gate()


@router.get(
    "/",
    summary="Get gate state",
    response_model=GateStateResponse,
)
def read_gate():
    """
    Get the gate current state
    """
    return GateStateResponse(state=gate.current_state)


@router.patch(
    "/",
    summary="Set gate state",
    response_model=GateStateResponse,
)
def set_status_light(
    state: Annotated[GateState, Form()], background_tasks: BackgroundTasks
):
    """
    Set the gate state
    """
    background_tasks.add_task(gate.set_status, state)
    return GateStateResponse(state=gate.current_state)
