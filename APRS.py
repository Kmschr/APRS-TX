import subprocess
import time
from datetime import datetime

# HAM License callsign
callsign = "KE0SPF"

# APRS Timestamp in format of Day/Hour/Minutes
zulutime = datetime.utcnow().strftime("%d%H%M")

# Latitude in format ddmm.hhN (i.e degrees, minutes, and hundredths of a minute north)
lat = "4033.08N"

# Longitude in format dddmm.hhW (i.e degrees, minutes, and hundreths of a minute west)
lon = "10505.41W"

# Altitude in format aaaaaa where altitude is in feet
alt = "005003"

comment = "CSU Rocket Team RPi Test UV-5R"

# Create complete APRS message
msg = "/{}z{}/{}-{} /A={}".format(zulutime, lat, lon, comment, alt)
print(msg)

# Create Audio file containing APRS packet
subprocess.call(["aprs", "-c", callsign, "-o", "packet.wav", msg])
# Play audio file
subprocess.run(["aplay", "packet.wav"])

