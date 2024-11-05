# LienHoa auto gate - Gate module API

API for controlling gate states (open/close, status lights, LCD screen,...).

![GitHub Tag](https://img.shields.io/github/v/tag/VinhNgT/lienhoa-gate-raspi-api?style=flat-square)

## Raspberry Pi Zero 2 Setup

**Note:** Use Raspberry Pi OS 32-bit because Zero 2 is slow af in 64-bit mode.

### Boot configuration

Add the following lines to `/boot/firmware/config.txt` or `/boot/config.txt` to configure hardware PWM, software I2C, and disable Bluetooth:

```ini
# Hardware PWM
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4

# Software I2C
dtoverlay=i2c-gpio,i2c_gpio_sda=23,i2c_gpio_scl=24,bus=8

# Disable Bluetooth, free up serial connection
dtoverlay=disable-bt
```

### Increase swap size and increase responsiveness

**Warning:** Use a "High Endurance" SD card, as intensive swap operations can quickly wear out standard cards.

- Edit `/etc/dphys-swapfile`
- Change `CONF_SWAPSIZE` to `512`
- Create a new file, `/etc/sysctl.d/90-swappiness.conf`
- Add to that file:

  ```conf
  vm.swappiness=5
  ```

- Reboot with `sudo reboot`

## Quick start

- Install docker: https://docs.docker.com/engine/install/raspberry-pi-os/
- Run `sudo usermod -aG docker $USER`
- Start services on boot:

  ```bash
  sudo systemctl enable docker.service
  sudo systemctl enable containerd.service
  ```

- Create file `/etc/docker/daemon.json` with content:

  ```json
  {
    "log-driver": "local"
  }
  ```

- Reboot with `sudo reboot`
- Run `docker compose up`
  - Note: You can use `docker compose up --build` to force build locally.
- Use examples in `insomnia_exports` to familiarize yourself, or go to http://raspberrypi/docs

## Manual start (not automatically start on boot, more error prone)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

sudo su
fastapi run app/main.py --port 80
```

Alternative non-root: https://www.geeksforgeeks.org/bind-port-number-less-1024-non-root-access/

## Upgrade packages:

```bash
pip freeze > requirements.txt
sed -i 's/==/>=/g' requirements.txt
pip install -r requirements.txt --upgrade
```
