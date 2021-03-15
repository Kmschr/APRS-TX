#!/usr/bin/env python3
#######################################################
# CSU ROCKET TEAM 2020-2021
# SRAD TELEMETRY COMPUTER
# RUNNING ON RPI-ZERO W/ CUSTOM PCB FOR ADAFRUIT SENSORS
# AND PWM AUDIO OUTPUT
#######################################################

import os
import sys
import math
import time
import board
import busio
import serial
import socket
import logging
import subprocess
import adafruit_gps
import adafruit_fxos8700
import adafruit_mpl3115a2
from gpiozero import LED

#######################################################
# PREVENT FROM RUNNING MULTIPLE TIMES ON A UNIX OS
# IF PROGRAM IS RUNNING FROM BOOT, CHECK HTOP AND KILL!
#######################################################

def get_lock(process_name):
    get_lock._lock_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    try:
        get_lock._lock_socket.bind('\0' + process_name)
    except socket.error:
        print('ERROR: PROGRAM IS ALREADY RUNNING, KILL IT BEFORE TRYING TO RUN AGAIN')
        sys.exit()

get_lock('aprs')

#######################################################
# LED & LOGGING SETUP
#######################################################

script_path = os.path.dirname(os.path.realpath(sys.argv[0]))

# GREEN - PROGRAM IS RUNNING
# BLUE - GPS FIX
# YELLOW - TRANSMITTING
# RED - ERROR
LED_GREEN = LED(22)
LED_RED = LED(23)
LED_BLUE = LED(5)
LED_YELLOW = LED(6)

LED_GREEN.on()

logging_format = logging.Formatter('%(asctime)s %(msecs)03dms | %(message)s',
                            datefmt='%Y-%m-%d %I:%M:%S%p')
root_logger = logging.getLogger()

file_handler = logging.FileHandler(script_path + '/bob.log')
file_handler.setFormatter(logging_format)
root_logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging_format)
root_logger.addHandler(console_handler)

root_logger.setLevel(logging.DEBUG)

logging.info('Program Started')

######################################################
# CONFIG + CONSTANTS
######################################################

CALLSIGN = 'KE0SPF'
APRS_COMMENT = 'CSU ROCKET TEAM'
APRS_SYMBOL_ROCKET = 'O'

######################################################
# SENSOR SETUP
######################################################

logging.info('Setting up sensors')

uart = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=10)
i2c = busio.I2C(board.SCL, board.SDA)

# Adafruit Ultimate GPS v3
gps_enabled = False
gps = None

try:
    gps = adafruit_gps.GPS(uart, debug=False)
    # Only send back GPRMC (Recommended Minimum Specific GNSS Sentence) and GPGGA (GPS Fix Data)
    gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')

    # Update once a second
    gps.send_command(b'PMTK220,1000')
    gps.update()

    logging.info('GPS Enabled')
    gps_enabled = True
except Exception as gps_exception:
    logging.info('GPS Disconnected')
    logging.info(str(gps_exception))

# Adafruit Barometric Altimeter MPL35115A2
altimeter_enabled = False
altimeter = None
try:
    altimeter = adafruit_mpl3115a2.MPL3115A2(i2c)
    altimeter.sealevel_pressure = 102520

    logging.info('Altimeter Enabled, Pressure: %d', altimeter.sealevel_pressure)
    altimeter_enabled = True
except Exception as altimeter_exception:
    logging.info('Altimeter Disconnected')
    logging.info(str(altimeter_exception))

# Adafruit 9-DOF Accelerometer
accelerometer_enabled = False
accelerometer = None
try:
    accelerometer = adafruit_fxos8700.FXOS8700(i2c)
    logging.info('9-DOF Enabled')
    accelerometer_enabled = True
except Exception as accelerometer_exception:
    logging.info('Accelerometer Disconnected')
    logging.info(str(accelerometer_exception))

############################################################
# TRANSMIT LOOP
############################################################

logging.info('Starting transmissions')

while True:

    # latitude in format ddmm.hhN (i.e degrees, minutes, and hundreths of a minute north)
    # longitude in format ddd.mm.hhW (i.e degrees, minutes, and hundreths of a minute west)
    # indeterminate position signaled by 0000.00N\00000.00W
    # altitude in format aaaaaa where altitude is in feet
    latitude = "0000.00N"
    longitude = "00000.00W"
    altitude = "000000"
    course = 0
    speed = 0

    # Accelerometer/Magnetometer readings
    ax = ay = az = "?"
    mx = my = mz = "?"

    if gps_enabled:
        try:
            if gps.update() and gps.has_fix:
                LED_BLUE.on()
                (latitude_min, latitude_deg) = math.modf(gps.latitude)
                (longitude_min, longitude_deg) = math.modf(gps.longitude)
                latitude_deg = '{:02d}'.format(abs(int(latitude_deg)))
                longitude_deg = '{:03d}'.format(abs(int(longitude_deg)))
                latitude_min = '{:05.2f}'.format(abs(round(latitude_min*60, 2)))
                longitude_min = '{:05.2f}'.format(abs(round(longitude_min*60, 2)))
                latitude = latitude_deg + latitude_min + 'N'
                longitude = longitude_deg + longitude_min + 'W'
                if gps.altitude_m is not None:
                    altitude = '{:06d}'.format(int(gps.altitude_m*3.28084))
                if gps.speed_knots is not None:
                    speed = int(gps.speed_knots)
                if gps.track_angle_deg is not None:
                    course = int(gps.track_angle_deg)
        except Exception as gps_error:
            LED_BLUE.off()
            logging.info('GPS gave error')
            logging.info(str(gps_error))

    if altimeter_enabled:
        pass
    if accelerometer_enabled:
        pass

    aprs_info = '!{}\\{}{}{:03d}/{:03d}/A={} {} a={},{},{}'.format(
            latitude,
            longitude,
            APRS_SYMBOL_ROCKET,
            course,
            speed,
            altitude,
            APRS_COMMENT,
            ax, ay, az
    )

    logging.info(aprs_info)

    subprocess.run([script_path + '/afsk/aprs',
                    '-c', CALLSIGN,
                    '--destination', 'APCSU1',
                    '--o', script_path + '/packet.wav',
                    aprs_info])



    LED_YELLOW.on()
    try:
        subprocess.run(['aplay',
                        '-q',
                         script_path + '/packet.wav'])
    except Exception as aplay_error:
        logging.info('aplay error')
        logging.info(str(aplay_error))
    LED_YELLOW.off()



