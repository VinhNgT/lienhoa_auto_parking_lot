import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from starlette.websockets import WebSocketState

from fastapi_app.base_module.button import Button, ButtonEvent
from fastapi_app.utils import RunOnShutdown, time_utils

button = Button(26)
RunOnShutdown.add(button.close)

router = APIRouter(
    prefix="/collision_button",
    tags=["button events"],
)


class CollisionButtonEvent(BaseModel):
    is_pressed: bool
    timestamp: str


@router.websocket("/watch")
async def watch_events(websocket: WebSocket):
    await websocket.accept()

    async def _wait_event():
        async with contextlib.aclosing(button.async_wait_event()) as wait_event:
            async for event in wait_event:
                try:
                    current_time = time_utils.get_utc_iso_now()
                    # print(event)

                    match event:
                        case ButtonEvent.PRESSED:
                            await websocket.send_json(
                                CollisionButtonEvent(
                                    is_pressed=True,
                                    timestamp=current_time,
                                ).model_dump()
                            )
                        case ButtonEvent.RELEASED:
                            await websocket.send_json(
                                CollisionButtonEvent(
                                    is_pressed=False,
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
