from contextlib import asynccontextmanager

import board
from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from fastapi_app.gpio_modules import SonarDistance


class DistanceSensor:
    def __init__(self):
        # self._sensor = LaserDistanceI2c(i2c_bus=7)
        self._sensor = SonarDistance(trigger_pin=board.D8, echo_pin=board.D7)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._sensor.__exit__(exc_type, exc_value, traceback)

    def get_distance(self) -> float:
        return self._sensor.get_distance()


class DistanceSensorResponse(BaseModel):
    distance: float


@asynccontextmanager
async def _lifespan(app: FastAPI):
    with DistanceSensor() as ds:
        global distance_sensor
        distance_sensor = ds
        yield


router = APIRouter(
    prefix="/distance_sensor",
    # tags=["distance_sensor (module VL53L0X)"],
    tags=["distance_sensor (module HC-SR04/HY-SRF05)"],
    lifespan=_lifespan,
)


@router.get(
    "/",
    summary="Get the distance sensor reading",
    response_model=DistanceSensorResponse,
)
def get_distance():
    return DistanceSensorResponse(distance=distance_sensor.get_distance())
