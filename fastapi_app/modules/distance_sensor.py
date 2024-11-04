import board
from fastapi import APIRouter
from pydantic import BaseModel

from fastapi_app.gpio_modules import SonarDistance


class DistanceSensor:
    def __init__(self):
        # self._sensor = LaserDistanceI2c(i2c_bus=7)
        self._sensor = SonarDistance(trigger_pin=board.D17, echo_pin=board.D27)

    def get_distance(self) -> float:
        return self._sensor.get_distance()


class DistanceSensorResponse(BaseModel):
    distance: float


router = APIRouter(
    prefix="/distance_sensor",
    # tags=["distance_sensor (module VL53L0X)"],
    tags=["distance_sensor (module HC-SR04/HY-SRF05)"],
)
distance_sensor = DistanceSensor()


@router.get(
    "/",
    summary="Get the distance sensor reading",
    response_model=DistanceSensorResponse,
)
def get_distance():
    return DistanceSensorResponse(distance=distance_sensor.get_distance())
