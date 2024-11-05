FROM python:3.11-bookworm

LABEL org.opencontainers.image.source=https://github.com/VinhNgT/lienhoa-gate-raspi-api

WORKDIR /code

RUN apt update && apt install -y libgpiod2

COPY ./pip.conf /root/.pip/pip.conf
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

COPY ./fastapi_app /code/fastapi_app
COPY ./version.txt /code/version.txt

CMD ["fastapi", "run", "fastapi_app/main.py", "--port", "80"]
