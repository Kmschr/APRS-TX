import board
import busio
import adafruit_fxos8700

i2c = busio.I2C(board.SCL, board.SDA)
fxos = adafruit_fxos8700.FXOS8700(i2c)

print(fxos.accelerometer)
