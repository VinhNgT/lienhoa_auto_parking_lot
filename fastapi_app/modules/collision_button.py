import asyncio
import contextlib
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from fastapi_app.base_module.button import Button, ButtonEvent
from fastapi_app.utils import CancelTasksOnShutdown

button = Button(26)


router = APIRouter(
    prefix="/collision_button",
    tags=["button events"],
)


class CollisionButtonEvent(BaseModel):
    is_pressed: bool
    time: str


@router.websocket("/watch")
async def watch_events(websocket: WebSocket):
    await websocket.accept()

    async def _wait_event():
        async with contextlib.aclosing(button.wait_event()) as wait_event:
            async for event in wait_event:
                try:
                    current_time = str(datetime.now())

                    match event:
                        case ButtonEvent.PRESSED:
                            # await websocket.send_text(
                            #     f"Button pressed! at {current_time}"
                            # )

                            await websocket.send_json(
                                CollisionButtonEvent(
                                    is_pressed=True,
                                    time=current_time,
                                ).model_dump()
                            )
                        case ButtonEvent.RELEASED:
                            # await websocket.send_text(
                            #     f"Button released! at {current_time}"
                            # )

                            await websocket.send_json(
                                CollisionButtonEvent(
                                    is_pressed=False,
                                    time=current_time,
                                ).model_dump()
                            )

                except WebSocketDisconnect:
                    break

    task = asyncio.create_task(_wait_event())
    CancelTasksOnShutdown.add(task)
    try:
        await task
    except asyncio.exceptions.CancelledError:
        pass
    finally:
        CancelTasksOnShutdown.remove(task)
