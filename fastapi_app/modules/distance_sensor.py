import asyncio
import contextlib

import board
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.websockets import WebSocketState

from fastapi_app.gpio_modules.ultrasonic_sensor import UltrasonicSensor
from fastapi_app.utils import RunOnShutdown, time_utils

sensor = UltrasonicSensor(board.D23, board.D24)
RunOnShutdown.add(sensor.close)

router = APIRouter(
    prefix="/distance_sensor",
    # tags=["distance_sensor (module VL53L0X)"],
    tags=["distance_sensor (module HC-SR04/HY-SRF05)"],
)


class DistanceSensorResponse(BaseModel):
    distance: float
    timestamp: str


@router.websocket("/watch")
async def watch_events(websocket: WebSocket, interval: float):
    await websocket.accept()
    sensor.set_sample_interval(interval)

    async def _wait_event():
        async with contextlib.aclosing(sensor.async_wait_event()) as wait_event:
            async for event in wait_event:
                try:
                    current_time = time_utils.get_utc_iso_now()
                    await websocket.send_json(
                        DistanceSensorResponse(
                            distance=event,
                            timestamp=current_time,
                        ).model_dump()
                    )

                except WebSocketDisconnect:
                    break

    task = asyncio.create_task(_wait_event())
    try:
        await task
    except asyncio.exceptions.CancelledError:
        # Hide exception message
        pass
    finally:
        if not websocket.application_state == WebSocketState.DISCONNECTED:
            await websocket.close(1001, reason="Another connection opened")
