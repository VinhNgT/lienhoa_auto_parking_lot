from fastapi import FastAPI, HTTPException, status
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager

from app.modules import status_lights, gate, screen, buzzer, distance_sensor
from app.exceptions import app_exceptions


@asynccontextmanager
async def lifespan(app: FastAPI):
    screen.screen.write_string("API ready")
    yield


app = FastAPI(
    title="LienHoa auto parking gate",
    version="1.0.3",
    summary="API điều khiển module Raspberry Pi Zero 2 cho dự án cổng tự động.",
    contact={
        "name": "Nguyễn Thế Vinh",
        "url": "https://github.com/VinhNgT",
        "email": "victorpublic0000@gmail.com",
    },
    lifespan=lifespan,
)


app.include_router(status_lights.router)
app.include_router(gate.router)
app.include_router(screen.router)
app.include_router(buzzer.router)
app.include_router(distance_sensor.router)


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


@app.exception_handler(app_exceptions.TooManyRequestsException)
async def buzzer_too_many_requests_exception_handler(request, exc):
    raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, str(exc))
