from __future__ import print_function
from myro import *

init('/dev/rfcomm0')
print (getName(), getBattery())
beep(.5, 440)
print (getEncoders(True))
turnRight(1, .5)
print (getEncoders(True))
turnLeft(1, .5)
print (getEncoders(True))
print (getMicEnvelope())
print (getAll())
p = takePicture()
savePicture(p, "test.jpg")
p = takePicture('color')
savePicture(p, "rawtest.jpg")
p = takePicture('gray')
savePicture(p, "graytest.jpg")
