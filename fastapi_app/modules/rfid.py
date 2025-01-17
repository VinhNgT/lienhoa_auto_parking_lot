import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.websockets import WebSocketState

from fastapi_app.gpio_modules.rfid_module import RfidModule as GPIORfid
from fastapi_app.modules.buzzer import buzzer
from fastapi_app.utils import RunOnShutdown, time_utils

rfid = GPIORfid(buzzer)
RunOnShutdown.add(rfid.close)

router = APIRouter(
    prefix="/rfid",
    tags=["rfid_module (module HC-SR04/HY-SRF05)"],
)


class RfidEventResponse(BaseModel):
    uid: str
    timestamp: str


@router.websocket("/watch")
async def watch_events(websocket: WebSocket):
    await websocket.accept()

    async def _wait_event():
        async with contextlib.aclosing(rfid.async_wait_event()) as wait_event:
            async for event in wait_event:
                try:
                    current_time = time_utils.get_utc_iso_now()
                    await websocket.send_json(
                        RfidEventResponse(
                            uid=event,
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
