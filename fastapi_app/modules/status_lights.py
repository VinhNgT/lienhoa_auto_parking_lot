from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Form
from pydantic import BaseModel, Field

from fastapi_app.gpio_modules import LedsI2c


class StatusLightState(str, Enum):
    NONE = "none"
    READY = "ready"
    PROCESSING = "processing"
    ALLOW = "allow"
    DENY = "deny"


class StatusLights:
    def __init__(self):
        self._leds = LedsI2c(i2c_bus=1, led_count=4)
        self.set_status(StatusLightState.NONE)

    def set_status(self, state: StatusLightState):
        match state:
            case StatusLightState.NONE:
                self._leds.set_leds_bits(0b0000)

            case StatusLightState.READY:
                self._leds.set_leds_bits(0b0001)

            case StatusLightState.PROCESSING:
                self._leds.set_leds_bits(0b0010)

            case StatusLightState.ALLOW:
                self._leds.set_leds_bits(0b0100)

            case StatusLightState.DENY:
                self._leds.set_leds_bits(0b1000)

        self.current_state = state


class StatusLightsStateResponse(BaseModel):
    state: StatusLightState = Field(
        description="The status light state",
        examples=["none", "ready", "processing", "allow", "deny"],
    )


router = APIRouter(
    prefix="/status_lights_state",
    tags=["status_lights_state (module PCF8574)"],
)
status_lights = StatusLights()


@router.get(
    "/",
    summary="Get status lights state",
    response_model=StatusLightsStateResponse,
)
def read_status_light():
    return StatusLightsStateResponse(state=status_lights.current_state)


@router.patch(
    "/",
    summary="Set status lights state",
    response_model=StatusLightsStateResponse,
)
def set_status_light(state: Annotated[StatusLightState, Form()]):
    status_lights.set_status(state)
    return StatusLightsStateResponse(state=status_lights.current_state)
