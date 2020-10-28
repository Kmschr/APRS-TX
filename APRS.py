import sys
import time
import threading
import subprocess
from datetime import datetime
from multiprocessing import Process

######################################################################
# OPTIONS
######################################################################

# HAM License callsign - MUST BE YOUR CALLSIGN
# NOT TRANSMITTING WITH YOUR CALLSIGN IS VIOLATION OF FCC
# AND YOU CAN BE FINED HEAVILY
CALLSIGN = 'KF0CDE'
APRS_COMMENT = 'CSU ROCKET TEAM TESTING '
APRS_SYMBOL_ROCKET = 'O'
TOTAL_TRANSMISSIONS = 3

######################################################################
# TRANSMIT LOOP
######################################################################

num_transmissions = 0
transmit_repeat = 20e9
play_time = time.time_ns() + transmit_repeat
start_time = play_time

while True:
    # APRS Timestamp in format of Day/Hour/Minutes zulu time
    zulutime = datetime.utcnow().strftime("%d%H%M")
    # latitude in format ddmm.hhN (i.e degrees, minutes, and hundredths of a minute north)
    lat = "4033.14N"
    # longitude in format dddmm.hhW (i.e degrees, minutes, and hundreths of a minute west)
    lon = "10505.69W"
    # altitude in format aaaaaa where altitude is in feet
    alt = "005003"
    # time and position format
    aprs_info = "/{}z{}\\{}{}{} /A={}".format(zulutime, lat, lon, APRS_SYMBOL_ROCKET, APRS_COMMENT + str(num_transmissions), alt)

    # write APRS message as wave audio file
    subprocess.run(["/home/pi/APRS-TX/afsk/aprs", "-c", CALLSIGN, "-o", "/home/pi/APRS-TX/packet"+str(num_transmissions)+".wav", aprs_info])
    aprs_end = time.time_ns()

    # make sure its been 2 seconds exactly before playing audio
    wait_time = (play_time - time.time_ns()) / 1e9
    if wait_time > 0:
        time.sleep(wait_time)
    else:
        print("APRS message is too long")
    print((time.time_ns() - start_time) / 1e9)

    # play APRS message over default soundcard
    proc = subprocess.Popen(["sudo aplay -q /home/pi/APRS-TX/packet"+str(num_transmissions)+".wav"], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True, start_new_session=True)
    play_time += transmit_repeat

    num_transmissions += 1

print((time.time_ns() - start_time) / 1e9)
