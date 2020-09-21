import sys
import time
import subprocess
from datetime import datetime

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

######################################################################
# OPTIONS
######################################################################

# HAM License callsign - MUST BE YOUR CALLSIGN
# NOT TRANSMITTING WITH YOUR CALLSIGN IS VIOLATION OF FCC
# AND YOU CAN BE FINED HEAVILY
CALLSIGN = 'KE0SPF'
APRS_COMMENT = 'CSU Rocket Team RPi Test UV-5R'
APRS_SYMBOL_ROCKET = '\O'
TOTAL_TRANSMIT_TIME_SEC = 60 * 5

######################################################################
# TRANSMIT LOOP
######################################################################

# APRS Timestamp in format of Day/Hour/Minutes zulu time
zulutime = datetime.utcnow().strftime("%d%H%M")

# Latitude in format ddmm.hhN (i.e degrees, minutes, and hundredths of a minute north)
lat = "4033.08N"

# Longitude in format dddmm.hhW (i.e degrees, minutes, and hundreths of a minute west)
lon = "10505.41W"

# Altitude in format aaaaaa where altitude is in feet
alt = "005003"

# Create complete APRS message
msg = "/{}z{}/{}{}{} /A={}".format(zulutime, lat, lon, APRS_SYMBOL_ROCKET, APRS_COMMENT, alt)
print(msg)

# Create Audio file containing APRS packet
subprocess.call(["aprs", "-c", CALLSIGN, "-o", "packet.wav", msg])
# Play audio file
subprocess.run(["aplay", "packet.wav"])
