import os

from gpiozero.pins.pigpio import PiGPIOFactory

IS_DOCKER = bool(os.getenv("IS_DOCKER", "False").capitalize() == "True")
DOCKER_HOSTNAME = "host.docker.internal"
print(f"IS_DOCKER: {IS_DOCKER}")

# out = subprocess.run(["ping", "-c", "1", DOCKER_HOSTNAME], capture_output=True)
# print(out.stdout.decode())
pi_gpio_factory = PiGPIOFactory(host=DOCKER_HOSTNAME if IS_DOCKER else None)
