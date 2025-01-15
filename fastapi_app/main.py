from contextlib import asynccontextmanager
from queue import Full

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse

from fastapi_app.modules import (
    buzzer,
    collision_button,
    distance_sensor,
    gate,
    rfid,
    screen,
    status_lights,
)

# Get the app's version number.
try:
    with open("version.txt", "r") as version_file:
        VERSION = version_file.read().strip()

except FileNotFoundError:
    VERSION = "0.0.1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    screen.screen.write_string("API ready")
    yield
    screen.screen.write_string("Server shutdown")


app = FastAPI(
    title="LienHoa auto gate - Gate module API",
    version=VERSION,
    summary="API điều khiển module Raspberry Pi Zero 2 cho dự án cổng tự động.",
    contact={
        "name": "Nguyễn Thế Vinh",
        "url": "https://github.com/VinhNgT",
        "email": "victorpublic0000@gmail.com",
    },
    lifespan=lifespan,
)


app.include_router(gate.router)
app.include_router(status_lights.router)
app.include_router(screen.router)
app.include_router(buzzer.router)
app.include_router(distance_sensor.router)
app.include_router(collision_button.router)
app.include_router(rfid.router)


@app.get(
    "/",
    summary="Welcome screen",
    tags=["pages"],
    response_class=PlainTextResponse,
)
def homescreen():
    return "Hello, World!"


@app.exception_handler(ValueError)
async def value_exception_handler(request, exc):
    raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


# @app.exception_handler(app_exceptions.TooManyRequestsException)
# async def buzzer_too_many_requests_exception_handler(request, exc):
#     raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc))


@app.exception_handler(Full)
async def buzzer_too_many_requests_exception_handler(request, exc):
    raise HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS, "Buzzer request queue is full"
    )
