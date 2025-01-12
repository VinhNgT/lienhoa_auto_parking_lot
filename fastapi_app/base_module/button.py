# ruff: noqa: F401

import asyncio

from gpiozero import Button, Device

from common import pi_gpio_factory

# button = Button(26)

# Use PiGPIO to avoid vscode freeze bug.
button = Button(26, pin_factory=pi_gpio_factory)


def wait_button_press():
    button.wait_for_press()
    print("The button was pressed!")
    button.wait_for_release()
    print("The button was released!")


async def main():
    print("Waiting for button press...")
    while True:
        await asyncio.to_thread(wait_button_press)


asyncio.run(main())
