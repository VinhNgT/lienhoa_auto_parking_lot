import asyncio
from enum import Enum
from typing import Annotated

from adafruit_extended_bus import ExtendedI2C as I2C
from fastapi import APIRouter, Form
from pydantic import BaseModel, Field

from fastapi_app.gpio_modules import LedsPcf8574
from fastapi_app.utils import RunOnShutdown

leds = LedsPcf8574(I2C(7), reverse_layout=True, led_count=4)
RunOnShutdown.add(leds.close)

leds_request_lock = asyncio.Lock()


class StatusLightState(str, Enum):
    NONE = "none"
    READY = "ready"
    PROCESSING = "processing"
    ALLOW = "allow"
    DENY = "deny"


class StatusLightsStateResponse(BaseModel):
    state: StatusLightState = Field(
        description="The status light state",
        examples=["none", "ready", "processing", "allow", "deny"],
    )


router = APIRouter(
    prefix="/status_lights_state",
    tags=["status_lights_state (module PCF8574)"],
)


# @router.get(
#     "/",
#     summary="Get status lights state",
#     response_model=StatusLightsStateResponse,
# )
# def read_status_light():
#     return StatusLightsStateResponse(state=status_lights.current_state)


@router.patch(
    "/",
    summary="Set status lights state",
    response_model=StatusLightsStateResponse,
)
async def set_status_light(state: Annotated[StatusLightState, Form()]):
    async with leds_request_lock:
        if state == StatusLightState.NONE:
            leds.set_leds_byte(0b0000)
        elif state == StatusLightState.READY:
            leds.set_leds_byte(0b1000)
        elif state == StatusLightState.PROCESSING:
            leds.set_leds_byte(0b0100)
        elif state == StatusLightState.ALLOW:
            leds.set_leds_byte(0b0010)
        elif state == StatusLightState.DENY:
            leds.set_leds_byte(0b0001)
        else:
            raise ValueError(f"Invalid state: {state}")

    return StatusLightsStateResponse(state=state)
