from pydantic import BaseModel
from fastapi import APIRouter, Form
from typing import Annotated
from gpio_modules.lcd_i2c import LcdI2c


class LcdScreen:
    def __init__(self):
        self.lcd = LcdI2c(i2c_bus=1)

    def write_string(self, text: str, format_string: bool):
        self.lcd.write_string(text, format_string=format_string)


class LcdFormData(BaseModel):
    text: str
    format: bool = True


class LcdResponse(BaseModel):
    text: str


router = APIRouter(
    prefix="/screen",
    tags=["screen"],
)
screen = LcdScreen()


@router.post(
    "/",
    summary="Set lcd screen text",
    response_model=LcdResponse,
)
def set_lcd_text(data: Annotated[LcdFormData, Form()]):
    """
    Set lcd screen text
    """
    screen.write_string(data.text, data.format)
    return LcdResponse(text=data.text)
