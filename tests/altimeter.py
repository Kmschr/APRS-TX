import board
import busio
import adafruit_mpl3115a2

i2c = busio.I2C(board.SCL, board.SDA)

print(i2c.scan())

sensor = adafruit_mpl3115a2.MPL3115A2(i2c)

print('Pressure: {0:0.3f} pascals'.format(sensor.pressure))
print('Altitude: {0:0.3f} meters'.format(sensor.altitude))
print('Temperature: {0:0.3f} degrees Celsius'.format(sensor.temperature))
