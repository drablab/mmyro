from __future__ import print_function

from myro import *

init('/dev/ttyUSB0')
print (getName())
beep(.5, 440)
print (getEncoders(True))
turnRight(1, .5)
print (getEncoders(True))
turnLeft(1, .5)
print (getEncoders(True))
print (getMicEnvelope())
print (getAll())

