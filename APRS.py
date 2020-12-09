######################################################################
# CSU ROCKET TEAM 2020-2021
# FLIGHT COMPUTER PROGRAM
# ROCKET: Aries CoVId
######################################################################

import os
import sys
import time
import math
import board
import busio
import signal
import serial
import logging
import argparse
import subprocess
import adafruit_gps
import adafruit_fxos8700
import adafruit_mpl3115a2
import RPi.GPIO as GPIO

script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
def signal_handler(sig, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

# Green indicates the program is running
# Yellow indicates a transmission occuring
# Red indicates one of the sensors is not giving data
# Blue indicates a fix for the GPS
LED_GREEN = 13
LED_RED = 16
LED_BLUE = 29
LED_YELLOW = 31

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(LED_GREEN, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(LED_RED, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(LED_BLUE, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(LED_YELLOW, GPIO.OUT, initial=GPIO.LOW)

logging.basicConfig(filename=script_path + '/aprs.log', 
                    format='%(asctime)s: %(message)s',
                    level=logging.DEBUG)

logging.info('Program Started')

######################################################################
# OPTIONS
######################################################################

parser = argparse.ArgumentParser(description='Transmit APRS information.')
parser.add_argument('callsign', type=str,
                    help='Your FCC HAM license callsign')
parser.add_argument('--without-gps', dest='gps', action='store_false',
                    help='No GPS')
parser.add_argument('--without-alt', dest='altimeter', action='store_false',
                    help='No altimeter')
parser.add_argument('--without-accelerometer', dest='accelerometer', action='store_false',
                    help='No accelerometer')
parser.set_defaults(gps=True)
parser.set_defaults(altimeter=True)
parser.set_defaults(accelerometer=True)
args = parser.parse_args()

CALLSIGN = args.callsign
APRS_COMMENT = 'CSU ROCKET TEAM TEST'
APRS_SYMBOL_ROCKET = 'O'
TRANSMIT_TIME_SECONDS = 20

print('Callsign:', CALLSIGN)
print('APRS_COMMENT:', APRS_COMMENT)
print('Transmit Timer: ' + str(TRANSMIT_TIME_SECONDS) + 's')
logging.info('Callsign: %s', CALLSIGN)
logging.info('APRS_COMMENT: %s', APRS_COMMENT)
logging.info('Transmit Timer: %s', str(TRANSMIT_TIME_SECONDS))

######################################################################
# SETUP SENSORS
######################################################################

# use Pi's mini UART and I2C for communicating with sensors
uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=10)
i2c = busio.I2C(board.SCL, board.SDA)

# Adafruit Ultimate GPS v3
gps = None
if args.gps:
    gps = adafruit_gps.GPS(uart, debug=False)

    # Only send back GPRMC (Recommended Minimum Specific GNSS Sentence) and GPGGA (GPS Fix Data)
    gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')

    # Update once a second
    gps.send_command(b'PMTK220,1000')
    gps.update()

    logging.info('GPS Enabled')

# Adafruit Barometric Altimeter MPL3115A2
altimeter = None
if args.altimeter:
    altimeter = adafruit_mpl3115a2.MPL3115A2(i2c)
    altimeter.sealevel_pressure = 102520

    logging.info('Altimeter Enabled, Pressure: %d', altimeter.sealevel_pressure)

# Adafruit 9-DOF Accelerometer
accelerometer = None
if args.accelerometer:
    accelerometer = adafruit_fxos8700.FXOS8700(i2c)

    logging.info('9-DOF Enabled')

######################################################################
# UPDATE LOOP
######################################################################

# initialize update info
num_updates = 0
last_update_time = time.time_ns()
start_time = last_update_time

# Update once a second, and transmit if it is the correct time to do so
while True:
    delta_time = time.time_ns() - last_update_time
    
    # once a second check
    if delta_time < 1e9:
        # go back to top of loop since it hasnt been a second yet
        continue

    # start timer for this update
    last_update_time = time.time_ns()

    elapsed = (last_update_time - start_time) / 1e9

    print('running... ({}s)'.format(elapsed))

    # latitude in format ddmm.hhN (i.e degrees, minutes, and hundredths of a minute north)
    # longitude in format dddmm.hhW (i.e degrees, minutes, and hundreths of a minute west)
    # indeterminate position signaled by 0000.00N\00000.00W
    # altitude in format aaaaaa where altitude is in feet
    latitude = "0000.00N"
    longitude = "00000.00W"
    altitude = 5003
    course = 0
    speed = 0

    # Acceleromter/Magnetometer readings
    ax = ay = az = 0
    mx = my = mz = "?"

    encountered_error = False

    try:
        # update info using GPS
        if gps is not None and gps.update() and gps.has_fix:
            GPIO.output(LED_BLUE, GPIO.HIGH)
            (latitude_min, latitude_deg) = math.modf(gps.latitude)
            (longitude_min, longitude_deg) = math.modf(gps.longitude)
            latitude_dir = 'N' if latitude_deg >= 0 else 'S'
            longitude_dir = 'W' if longitude_deg <= 0 else 'E'
            latitude_deg = '{:02d}'.format(abs(int(latitude_deg)))
            longitude_deg = '{:03d}'.format(abs(int(longitude_deg)))
            latitude_min = '{:05.2f}'.format(abs(round(latitude_min*60, 2)))
            longitude_min = '{:05.2f}'.format(abs(round(longitude_min*60, 2)))
            latitude = latitude_deg + latitude_min + latitude_dir
            longitude = longitude_deg + longitude_min + longitude_dir
            if gps.altitude_m is not None:
                altitude = int(gps.altitude_m*3.28084)
            if gps.speed_knots is not None:
                speed = int(gps.speed_knots)
            if gps.track_angle_deg is not None:
                course = int(gps.track_angle_deg)
        else:
            GPIO.output(LED_BLUE, GPIO.LOW)
    except OSError:
        logging.info('GPS Error')
        encountered_error = True

    try:
        # update info using altimeter
        if altimeter is not None:
            altitude = int(altimeter.altitude*3.28084)
    except OSError:
        logging.info('altimeter error')
        encountered_error = True

    # update info using accelerometer
    try:
        if accelerometer is not None:
            ax, ay, az = accelerometer.accelerometer
            mx, my, mz = accelerometer.magnetometer
    except OSError:
        logging.info('accelerometer error')
        encountered_error = True

    # indicate any errors with sensor data
    if encountered_error:
        GPIO.ouptut(LED_RED, GPIO.HIGH)
    else:
        GPIO.output(LED_RED, GPIO.LOW)

    logging.info('Updated: %s, %s  %dft', latitude, longitude, altitude)

    if num_updates % TRANSMIT_TIME_SECONDS == 0:
        GPIO.output(LED_YELLOW, GPIO.HIGH)

        logging.info('transmitting')

        subprocess.run([script_path + "/baa",
                        "-c", CALLSIGN,
                        "--lat", latitude,
                        "--lng", longitude,
                        "--course", str(course),
                        "--speed", str(speed),
                        "--alt", str(altitude)])

        GPIO.output(LED_YELLOW, GPIO.LOW)

    num_updates += 1
