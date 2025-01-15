import asyncio
from typing import Annotated

from fastapi import APIRouter, Form
from pydantic import BaseModel, Field

from fastapi_app.base_module import LcdI2c
from fastapi_app.utils import RunOnShutdown

screen = LcdI2c(i2c_bus=8)
RunOnShutdown.add(screen.close)

# Lock to prevent multiple request from accessing the screen at the same time
screen_request_lock = asyncio.Lock()


class LcdFormData(BaseModel):
    text: str = Field(
        description="Text to display on the screen",
        examples=["Hello, World!"],
    )


class LcdResponse(BaseModel):
    text: str


router = APIRouter(
    prefix="/screen",
    tags=["screen (module 2004A with PCF8574 I2C backpack)"],
)


@router.post(
    "/",
    summary="Set lcd screen text",
    response_model=LcdResponse,
)
async def set_lcd_text(data: Annotated[LcdFormData, Form()]):
    async with screen_request_lock:
        screen.write_string(data.text)
    return LcdResponse(text=data.text)
