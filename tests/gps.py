import time
import serial
import adafruit_gps

uart = serial.Serial('/dev/ttyS0', baudrate=9600, timeout=10)

gps = adafruit_gps.GPS(uart, debug=False)
gps.send_command(b"PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0")
gps.send_command(b"PMTK220,1000")

while True:
    gps.update()

    while not gps.has_fix:
        print('no fix')
        gps.update()
        time.sleep(1)

    print('fixed')
    print(gps.latitude, gps.longitude)
    print(gps.altitude_m)
    time.sleep(5)

