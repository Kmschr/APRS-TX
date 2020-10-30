# APRS-TX
APRS transmission from a Raspberry Pi interfaced w/ HT over standard audio output

## Installation and Setup

[GPS Wiring (Pi's UART)](https://learn.adafruit.com/adafruit-ultimate-gps/circuitpython-parsing)

Clone this repository and go into it

`$ git clone https://github.com/Kmschr/APRS-TX`

`$ cd APRS-TX`

Install dependencies

`$ pip3 install -r requirements.txt`

Ensure pi output is set to analog/headphones (NOT HDMI)

`$ alsamixer`

### Running normally

`$ python3 APRS.py YOUR_CALLSIGN`

### Running without the GPS attached

`$ python3 APRS.py YOUR_CALLSIGN --without-gps`

## Example cronjob

For automatic startup when pi is turned on

`$ crontab -e`

```
XDG_RUNTIME_DIR=/run/user/1000
@reboot python3 /home/pi/APRS-TX/APRS.py KE0SPF &
```
