import time
import serial
s = serial.Serial("/dev/rfcomm0", timeout=10)
time.sleep(3)
s.write('NNNNNNNNN')
print(s.read(9))
print(s.read(8))
