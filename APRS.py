######################################################################
# CSU ROCKET TEAM 2020-2021
# FLIGHT COMPUTER PROGRAM
# ROCKET: Aries CoVId
######################################################################

import os
import sys
import time
import math
import busio
import signal
import serial
import yaspin
import argparse
import subprocess
import adafruit_gps
from yaspin import yaspin, kbi_safe_yaspin
from datetime import datetime

script_path = os.path.dirname(os.path.realpath(sys.argv[0]))
def signal_handler(sig, frame):
    print('exiting')
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

######################################################################
# OPTIONS
######################################################################

parser = argparse.ArgumentParser(description='Transmit APRS information.')
parser.add_argument('callsign', type=str,
                    help='Your FCC HAM license callsign')
parser.add_argument('--with-gps', dest='gps', action='store_true',
                    help='The Adafruit GPS is hooked up')
parser.add_argument('--without-gps', dest='gps', action='store_false',
                    help='No GPS')
parser.set_defaults(gps=True)
args = parser.parse_args()

CALLSIGN = args.callsign
APRS_COMMENT = 'CSU ROCKET TEAM GPS TESTING'
APRS_SYMBOL_ROCKET = 'O'
TRANSMIT_TIME_SECONDS = 65

print('Callsign: ' + CALLSIGN)
print('APRS_COMMENT: ' + APRS_COMMENT)
print('Transmit Timer: ' + str(TRANSMIT_TIME_SECONDS) + 's')

######################################################################
# SETUP SENSORS
######################################################################

gps = None
# Adafruit Ultimate GPS v3
if args.gps:
    uart = serial.Serial("/dev/ttyS0", baudrate=9600, timeout=10)
    gps = adafruit_gps.GPS(uart, debug=False)
    gps.send_command(b'PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0')
    gps.send_command(b'PMTK220,500')
    gps.update()

    with yaspin(text="Waiting for GPS") as sp:
        while not gps.has_fix:
            gps.update()
            time.sleep(0.5)

######################################################################
# TRANSMIT LOOP
######################################################################

num_transmissions = 0
transmit_repeat = TRANSMIT_TIME_SECONDS * 1e9
play_time = time.time_ns() + 2e9
start_time = play_time

color = ("red", "white", "green", "blue")
spinner = kbi_safe_yaspin(text="")
spinner.start()

while True:
    # APRS Timestamp in format of Day/Hour/Minutes zulu time
    zulutime = datetime.utcnow().strftime("%d%H%M")

    # latitude in format ddmm.hhN (i.e degrees, minutes, and hundredths of a minute north)
    # longitude in format dddmm.hhW (i.e degrees, minutes, and hundreths of a minute west)
    # indeterminate position signaled by 0000.00N\00000.00W
    # altitude in format aaaaaa where altitude is in feet
    latitude = "0000.00N"
    longitude = "00000.00W"
    altitude = "005003"

    if gps is not None and gps.update():
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
            altitude = '{:06d}'.format(int(gps.altitude_m*3.28084))

    # time and position format
    aprs_info = '/{}z{}\\{}{}{} /A={}'.format(zulutime, 
                                              latitude, 
                                              longitude, 
                                              APRS_SYMBOL_ROCKET, 
                                              APRS_COMMENT, 
                                              altitude)

    spinner.text = CALLSIGN + '>APRS,WIDE1-1,WIDE2-1:' + aprs_info
    spinner.color = color[num_transmissions % 4]

    # write APRS message as wave audio file
    subprocess.run([script_path + "/afsk/aprs", 
                    "-c", CALLSIGN, "-o", 
                    "/tmp/packet"+str(num_transmissions%3)+".wav", 
                    aprs_info])
    aprs_end = time.time_ns()

    # make sure its been required seconds exactly before playing audio
    wait_time = (play_time - time.time_ns()) / 1e9
    if wait_time > 0:
        time.sleep(wait_time)
    else:
        print("APRS message is too long")
    #print((time.time_ns() - start_time) / 1e9)

    # play APRS message over default soundcard in new non-blocking process
    subprocess.Popen(["sudo aplay -q /tmp/packet"+str(num_transmissions%3)+".wav"], 
                     shell=True, 
                     stdin=None, 
                     stdout=None, 
                     stderr=None, 
                     close_fds=True, 
                     start_new_session=True)
    play_time += transmit_repeat

    num_transmissions += 1
