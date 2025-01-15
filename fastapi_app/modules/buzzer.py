from typing import Annotated

from fastapi import APIRouter, Form
from gpiozero.tones import Tone
from pydantic import BaseModel, Field

from fastapi_app.base_module import Buzzer as GPIOBuzzer
from fastapi_app.base_module import BuzzerPlayRequest
from fastapi_app.utils import RunOnShutdown

buzzer = GPIOBuzzer(21)
RunOnShutdown.add(buzzer.close)


class BuzzerFormData(BaseModel):
    frequency: float = Field(
        description="Frequency in Hz",
        examples=[600, 1000],
        ge=buzzer.min_frequency,
        le=buzzer.max_frequency,
    )
    duration: float = Field(
        description="Duration in seconds",
        examples=[0.5, 1.0],
        ge=0.01,
        le=5,
    )


router = APIRouter(
    prefix="/buzzer",
    tags=["buzzer (passive)"],
)


@router.post(
    "/",
    summary="Set buzzer frequency and duration",
    response_model=BuzzerFormData,
)
def set_buzzer(data: Annotated[BuzzerFormData, Form()]):
    tone = Tone(data.frequency)
    buzzer.schedule(BuzzerPlayRequest(tone, data.duration), block=False)

    return data
