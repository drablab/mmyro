from __future__ import print_function
"""
Myro Base Classes.
(c) 2006, Institute for Personal Robots in Education
http://www.roboteducation.org/
Distributed under a Shared Source License
"""

__REVISION__ = "$Revision: 1730 $"
__VERSION__  = "5.0.1"
__AUTHOR__   = "Doug Blank <dblank@cs.brynmawr.edu>"


import sys, atexit, time, random, pickle, threading, os, types, copy
import traceback, urllib, glob
import myro.globvars
from myro.media import *
from myro.system import *

# Check versions of things:
_pil_version = None
try:
    import PIL.Image as Image
    _pil_version = Image.VERSION
    del Image
except:
    print ("ERROR: you need to install Python Image Library to make pictures", file=sys.stderr)
if _pil_version != None:
    if _pil_version.split(".") < ["1", "1", "5"]:
        print("ERROR: you need to upgrade Python Image Library to at least 1.1.5 (you're running %s)" % _pil_version, file=sys.stderr)
del _pil_version

def timer(seconds=0):
    """ A function to be used with 'for' """
    start = time.time()
    while True:
        timepast = time.time() - start
        if seconds != 0 and timepast > seconds:
            raise StopIteration()
        yield round(timepast, 3)

_timers = {}
def timeRemaining(seconds=0):
    """ Function to be used with 'while' """
    global _timers
    if seconds == 0: return True
    now = time.time()
    stack = traceback.extract_stack()
    filename, line_no, q1, q2 = stack[-2]
    if filename.startswith("<pyshell"):
        filename = "pyshell"
    if (filename, line_no) not in _timers:
        _timers[(filename, line_no)] = (now, seconds)
        return True
    start, duration = _timers[(filename, line_no)]
    if seconds != duration:
        _timers[(filename, line_no)] = (now, seconds)
        return True
    if now - start > duration:
        del _timers[(filename, line_no)]
        return False
    else:
        return True

pickled = None

def wait(seconds):
    """
    Wrapper for time.sleep() so that we may later overload.
    """
    return time.sleep(seconds)

def currentTime():
    """
    Returns current time in seconds since 
    """
    return time.time()

def pickOne(*args):
    """
    Randomly pick one of a list, or one between [0, arg).
    """
    if len(args) == 1:
        return random.randrange(args[0])
    else:
        return args[random.randrange(len(args))]

def pickOneInRange(start, stop):
    """
    Randomly pick one of a list, or one between [0, arg).
    """
    return random.randrange(start, stop)

def heads(): return flipCoin() == "heads"
def tails(): return flipCoin() == "tails"

def flipCoin():
    """
    Randomly returns "heads" or "tails".
    """
    return ("heads", "tails")[random.randrange(2)]

def randomNumber():
    """
    Returns a number between 0 (inclusive) and 1 (exclusive).
    """
    return random.random()

def ask(prompt):
    return raw_input(prompt)

class BackgroundThread(threading.Thread):
    """
    A thread class for running things in the background.
    """
    def __init__(self, function, pause = 0.01):
        """
        Constructor, setting initial variables
        """
        self.function = function
        self._stopevent = threading.Event()
        self._sleepperiod = pause
        threading.Thread.__init__(self, name="MyroThread")
        
    def run(self):
        """
        overload of threading.thread.run()
        main control loop
        """
        while not self._stopevent.isSet():
            self.function()
            #self._stopevent.wait(self._sleepperiod)

    def join(self,timeout=None):
        """
        Stop the thread
        """
        self._stopevent.set()
        threading.Thread.join(self, timeout)

class Robot(object):
    _app = None
    _joy = None
    _cal = None
    def __init__(self):
        """
        Base robot class.
        """
        self.lock = threading.Lock()
    
    def translate(self, amount):
        raise AttributeError("this method needs to be written")

    def rotate(self, amount):
        raise AttributeError("this method needs to be written")

    def move(self, translate, rotate):
        raise AttributeError("this method needs to be written")

    def beep(self, duration, frequency1, frequency2 = None):
        raise AttributeError("this method needs to be written")
        
    def getLastSensors(self):
        """ Should not get the current, but the last. This is default behavior. """
        return self.get("all")

    def update(self):
        """ Update the robot """
        raise AttributeError("this method needs to be written")

### The rest of these methods are just rearrangements of the above

    def getVersion(self):
        """ Returns robot version information. """
        return self.get("version")

    def getLight(self, *position):
        """ Return the light readings. """
        return self.get("light", *position)

    def getIR(self, *position):
        """ Returns the infrared readings. """
        return self.get("ir", *position)
    
    def getDistance(self, *position):
        """ Returns the S2 Distance readings. """
        return self.getDistance(*position)

    def getLine(self, *position):
        """ Returns the line sensor readings. """
        return self.get("line", *position)

    def getStall(self):
        """ Returns the stall reading. """
        return self.get("stall")

    def getInfo(self, *item):
        """ Returns the info. """
        retval = self.get("info", *item)
        retval["myro"] =  __VERSION__
        return retval

    def getName(self):
        """ Returns the robot's name. """
        return self.get("name")

    def getPassword(self):
        """ Returns the robot's password. """
        return self.get("password")

    def getForwardness(self):
        """ Returns the robot's directionality. """
        return self.get("forwardness")

    def getAll(self):
        return self.get("all")

    def setLED(self, position, value):
        return self.set("led", position, value)
        
    def setName(self, name):
        return self.set("name", name)

    def setPassword(self, password):
        return self.set("password", password)

    def setForwardness(self, value):
        return self.set("forwardness", value)
    
    def setVolume(self, value):
        return self.set("volume", value)

    def setStartSong(self, songName):
        return self.set("startsong", songName)

    def forward(self, speed=1, interval=None):
        self.move(speed, 0)
        if interval != None:
            time.sleep(interval)
            self.stop()

    def backward(self, speed=1, interval=None):
        self.move(-speed, 0)
        if interval != None:
            time.sleep(interval)
            self.stop()

    def turn(self, direction, value = .8, interval=None):
        if type(direction) in [float, int]:
            retval = self.move(0, direction)
        else:
            direction = direction.lower()
            if direction == "left":
                retval = self.move(0, value)
            elif direction == "right":
                retval = self.move(0, -value)
            elif direction in ["straight", "center"]:
                retval = self.move(0, 0) # aka, stop!
            else:
                retval = "error"
        if interval != None:
            time.sleep(interval)
            self.stop()
        return retval

    def turnLeft(self, speed=1, interval=None):
        retval = self.move(0, speed)
        if interval != None:
            time.sleep(interval)
            self.stop()
        return retval
    
    def turnRight(self, speed=1, interval=None):
        retval = self.move(0, -speed)
        if interval != None:
            time.sleep(interval)
            self.stop()
        return retval

    def stop(self):
        return self.move(0, 0)

    def motors(self, left, right):
        trans = (right + left) / 2.0
        rotate = (right - left) / 2.0
        return self.move(trans, rotate)

    def restart(self):
        pass
    def close(self):
        pass
    def open(self):
        pass
    def playSong(self, song, wholeNoteDuration = .545):
        """ Plays a song [(freq, [freq2,] duration),...] """
        # 1 whole note should be .545 seconds for normal
        for tuple in song:
            self.playNote(tuple, wholeNoteDuration)

    def playNote(self, tuple, wholeNoteDuration = .545):
        if len(tuple) == 2:
            (freq, dur) = tuple
            self.beep(dur * wholeNoteDuration, freq)
        elif len(tuple) == 3:
            (freq1, freq2, dur) = tuple
            self.beep(dur * wholeNoteDuration, freq1, freq2)
# functions:
def _cleanup():
    if myro.globvars.robot:
            if "robot" in myro.globvars.robot.robotinfo:
                try:
                    myro.globvars.robot.stop() # hangs?
                    time.sleep(0.5)                        
                except: # catch serial.SerialException
                    # port already closed
                    pass
            try:
                myro.globvars.robot.close()
            except:
                pass

import signal

def ctrlc_handler(signum, frame):
    if myro.globvars.robot:
        #myro.globvars.robot.open()
        #print "done opening"
        myro.globvars.robot.manual_flush()
        if "robot" in myro.globvars.robot.robotinfo:
            myro.globvars.robot.hardStop()
    #raise KeyboardInterrupt
    orig_ctrl_handler()

orig_ctrl_handler = signal.getsignal(signal.SIGINT)
# Set the signal handler and a 5-second alarm
signal.signal(signal.SIGINT, ctrlc_handler)

# Get ready for user prompt; set up environment:
if not myro.globvars.setup:
    myro.globvars.setup = 1
    atexit.register(_cleanup)
    # Ok, now we're ready!
    print ("(c) 2006-2007 Institute for Personal Robots in Education",  file=sys.stderr)
    print ("[See http://www.roboteducation.org/ for more information]",  file=sys.stderr)
    print ("Myro version %s is ready!" % (__VERSION__, ),  file=sys.stderr)

## Functional interface:

def requestStop():
    if myro.globvars.robot:
        myro.globvars.robot.requestStop = 1
def initialize(id = None):
    myro.globvars.robot = Scribbler(id)
    __builtins__["robot"] = myro.globvars.robot

init = initialize        

def translate(amount):
    if myro.globvars.robot:
        return myro.globvars.robot.translate(amount)
    else:
        raise AttributeError("need to initialize robot")
def rotate(amount):
    if myro.globvars.robot:
        return myro.globvars.robot.rotate(amount)
    else:
        raise AttributeError("need to initialize robot")
def move(translate, rotate):
    if myro.globvars.robot:
        return myro.globvars.robot.move(translate, rotate)
    else:
        raise AttributeError("need to initialize robot")
def forward(speed=1, seconds=None):
    if myro.globvars.robot:
        return myro.globvars.robot.forward(speed, seconds)
    else:
        raise AttributeError("need to initialize robot")
    
def backward(speed=1, seconds=None):
    if myro.globvars.robot:
        return myro.globvars.robot.backward(speed, seconds)
    else:
        raise AttributeError("need to initialize robot")
def turn(direction, amount = .8, seconds=None):
    if myro.globvars.robot:
        return myro.globvars.robot.turn(direction, amount, seconds)
    else:
        raise AttributeError("need to initialize robot")
def turnLeft(speed=1, seconds=None):
    if myro.globvars.robot:
        return myro.globvars.robot.turnLeft(speed, seconds)
    else:
        raise AttributeError("need to initialize robot")
def turnRight(speed=1, seconds=None):
    if myro.globvars.robot:
        return myro.globvars.robot.turnRight(speed, seconds)
    else:
        raise AttributeError("need to initialize robot")
def stop():
    if myro.globvars.robot:
        return myro.globvars.robot.stop()
def getPosition():
    """This returns the x and y coordinates of the scribbler 2"""   
    if myro.globvars.robot:
        return myro.globvars.robot.getPosition()
    else:
        raise AttributeError("need to initialize robot")    
def hereIs(x=0, y=0):
    if myro.globvars.robot:
        return myro.globvars.robot.setHereIs(x, y)
    else:
        raise AttributeError("need to initialize robot")
def getAngle():
    """This returns the current angle of the scribbler 2"""   
    if myro.globvars.robot:
        return myro.globvars.robot.getAngle()
    else:
        raise AttributeError("need to initialize robot")        
def setAngle(angle):
    if myro.globvars.robot:
        return myro.globvars.robot.setAngle(angle)
    else:
        raise AttributeError("need to initialize robot")    
def beginPath():
    """Speed can be a value from 1 to 15"""   
    if myro.globvars.robot:
        return myro.globvars.robot.setBeginPath()
    else:
        raise AttributeError("need to initialize robot")
def moveTo(x, y):
    if myro.globvars.robot:
        return myro.globvars.robot.setMove(x, y, "to")
    else:
        raise AttributeError("need to initialize robot")
def moveBy(x, y):
    if myro.globvars.robot:
        return myro.globvars.robot.setMove(x, y, "by")
    else:
        raise AttributeError("need to initialize robot")    
def turnTo(angle, radsOrDegrees):
    if myro.globvars.robot:
        return myro.globvars.robot.setTurn(angle, "to", radsOrDegrees)
    else:
        raise AttributeError("need to initialize robot") 
def turnBy(angle, radsOrDegrees):
    if myro.globvars.robot:
        return myro.globvars.robot.setTurn(angle, "by", radsOrDegrees)
    else:
        raise AttributeError("need to initialize robot")
def arcTo(x, y, radius):
    if myro.globvars.robot:
        return myro.globvars.robot.setArc(x, y, radius, "to")
    else:
        raise AttributeError("need to initialize robot")
def arcBy(x, y, radius):
    if myro.globvars.robot:
        return myro.globvars.robot.setArc(x, y, radius, "by")
    else:
        raise AttributeError("need to initialize robot")
def endPath():
    if myro.globvars.robot:
        return myro.globvars.robot.setEndPath()
    else:
        raise AttributeError("need to initialize robot")
def getMicEnvelope():
    """Returns a number representing the microphone envelope noise"""   
    if myro.globvars.robot:
        return myro.globvars.robot.getMicEnvelope()
    else:
        raise AttributeError("need to initialize robot") 
def getMotorStats():
    '''Return the current motion status as a packed long and single additional byte showing if motors are ready for commands (1=ready, 0=busy):
 Left wheel and right wheel are signed, twos complement eight bit velocity values,
 Idler timer is the time in 1/10 second since the last idler edge,
 Idler spd is an unsigned six-bit velocity value, and
 Mov is non-zero iff one or more motors are turning.
 Left and right wheel velocities are instanteous encoder counts over a 1/10-second interval.
 Idler wheel wheel velocity is updated every 1/10 second and represents the idler encoder count during the last 1.6 seconds.'''   
    if myro.globvars.robot:
        return myro.globvars.robot.getMotorStats()
    else:
        raise AttributeError("need to initialize robot") 
def getEncoders(zeroEncoders=False):
    '''Gets the values for the left and right encoder wheels.  Negative value means they have moved
    backwards from the robots perspective.  Each turn of the encoder wheel is counted as and increment or
    decrement of 2 depending on which direction the wheels moved.  
    if zeroEncoders is set to True then the encoders will be set to zero after reading the values'''
    if myro.globvars.robot:
        return myro.globvars.robot.getEncoders(zeroEncoders)
    else:
        raise AttributeError("need to initialize robot")   
def openConnection():
    if myro.globvars.robot:
        return myro.globvars.robot.open()
    else:
        raise AttributeError("need to initialize robot")
def closeConnection():
    if myro.globvars.robot:
        return myro.globvars.robot.close()
    else:
        raise AttributeError("need to initialize robot")
def get(sensor = "all", *pos):
    if myro.globvars.robot:
        return myro.globvars.robot.get(sensor, *pos)
    else:
        raise AttributeError("need to initialize robot")
def getVersion():
    if myro.globvars.robot:
        return myro.globvars.robot.get("version")
    else:
        raise AttributeError("need to initialize robot")
def getLight(*pos):
    if myro.globvars.robot:
        return myro.globvars.robot.get("light", *pos)
    else:
        raise AttributeError("need to initialize robot")
def getIR(*pos):
    if myro.globvars.robot:
        return myro.globvars.robot.get("ir", *pos)
    else:
        raise AttributeError("need to initialize robot")

def getDistance(*pos):
    if myro.globvars.robot:
        return myro.globvars.robot.getDistance(*pos)
    else:
        raise AttributeError("need to initialize robot")
def getLine(*pos):
    if myro.globvars.robot:
        return myro.globvars.robot.get("line", *pos)
    else:
        raise AttributeError("need to initialize robot")
def getStall():
    if myro.globvars.robot:
        return myro.globvars.robot.get("stall")
    else:
        raise AttributeError("need to initialize robot")
def getInfo(*item):
    if myro.globvars.robot:
        retval = myro.globvars.robot.getInfo(*item)
        retval["myro"] =  __VERSION__
        return retval
    else:
        return {"myro": __VERSION__}
def getAll():
    if myro.globvars.robot:
        return myro.globvars.robot.get("all")
    else:
        raise AttributeError("need to initialize robot")
def getName():
    if myro.globvars.robot:
        return myro.globvars.robot.get("name")
    else:
        raise AttributeError("need to initialize robot")
def getPassword():
    if myro.globvars.robot:
        return myro.globvars.robot.get("password")
    else:
        raise AttributeError("need to initialize robot")
def getForwardness():
    if myro.globvars.robot:
        return myro.globvars.robot.get("forwardness")
    else:
        raise AttributeError("need to initialize robot")
def getStartSong():
    if myro.globvars.robot:
        return myro.globvars.robot.get("startsong")
    else:
        raise AttributeError("need to initialize robot")
def getVolume():
    if myro.globvars.robot:
        return myro.globvars.robot.get("volume")
    else:
        raise AttributeError("need to initialize robot")
def update():
    if myro.globvars.robot:
        return myro.globvars.robot.update()
    else:
        raise AttributeError("need to initialize robot")
def beep(duration=.5, frequency1=None, frequency2=None):
    if type(duration) in [tuple, list]:
        frequency2 = frequency1
        frequency1 = duration
        duration =.5
    if frequency1 == None:
        frequency1 = random.randrange(200, 10000)
    if type(frequency1) in [tuple, list]:
        if frequency2 == None:
            frequency2 = [None for i in range(len(frequency1))]
        for (f1, f2) in zip(frequency1, frequency2):
            if myro.globvars.robot:
                myro.globvars.robot.beep(duration, f1, f2)
            else:
                computer.beep(duration, f1, f2)
    else:
        if myro.globvars.robot:
            myro.globvars.robot.beep(duration, frequency1, frequency2)
        else:
            computer.beep(duration, frequency1, frequency2)

def scaleDown(loopCount):
    beep(0.5, 9000 - 200 * loopCount)

def scaleUp(loopCount):
    beep(0.5, 200 + 200 * loopCount)

def set(item, position, value = None):
    if myro.globvars.robot:
        return myro.globvars.robot.set(item, position, value)
    else:
        raise AttributeError("need to initialize robot")
def setLED(position, value):
    if myro.globvars.robot:
        return myro.globvars.robot.set("led", position, value)
    else:
        raise AttributeError("need to initialize robot")
def setName(name):
    if myro.globvars.robot:
        return myro.globvars.robot.set("name", name)
    else:
        raise AttributeError("need to initialize robot")
def setPassword(password):
    if myro.globvars.robot:
        return myro.globvars.robot.set("password", password)
    else:
        raise AttributeError("need to initialize robot")
def setForwardness(value):
    if myro.globvars.robot:
        return myro.globvars.robot.set("forwardness", value)
    else:
        raise AttributeError("need to initialize robot")
def setVolume(value):
    if myro.globvars.robot:
        return myro.globvars.robot.set("volume", value)
    else:
        raise AttributeError("need to initialize robot")
def setS2Volume(value):
    """Level can be between 0-100 and represents the percent volume level of the speaker"""   
    if myro.globvars.robot:
        return myro.globvars.robot.setS2Volume(value)
    else:
        raise AttributeError("need to initialize robot")    
def setStartSong(songName):
    if myro.globvars.robot:
        return myro.globvars.robot.set("startsong", songName)
    else:
        raise AttributeError("need to initialize robot")
def motors(left, right):
    if myro.globvars.robot:
        return myro.globvars.robot.motors(left, right)
    else:
        raise AttributeError("need to initialize robot")
def restart():
    if myro.globvars.robot:
        return myro.globvars.robot.restart()
    else:
        raise AttributeError("need to initialize robot")
def joyStick(showSensors = 0):
    if myro.globvars.robot:
        return Joystick(myro.globvars.robot, showSensors)
    else:
        raise AttributeError("need to initialize robot")
def calibrate():
    if myro.globvars.robot:
        return Calibrate(myro.globvars.robot)
    else:
        raise AttributeError("need to initialize robot")
def playSong(song, wholeNoteDuration = .545):
    if myro.globvars.robot:
        return myro.globvars.robot.playSong(song, wholeNoteDuration)
    else:
        raise AttributeError("need to initialize robot")
def playNote(tup, wholeNoteDuration = .545):
    if myro.globvars.robot:
        return myro.globvars.robot.playNote(tup, wholeNoteDuration)
    else:
        raise AttributeError("need to initialize robot")

########################### New dongle commands

def getBright(position=None):
    if myro.globvars.robot:
        return myro.globvars.robot.getBright(position)
    else:
        raise AttributeError("need to initialize robot")

def getBlob():
    if myro.globvars.robot:
        return myro.globvars.robot.getBlob()
    else:
        raise AttributeError("need to initialize robot")

def getObstacle(position=None):
    if myro.globvars.robot:
        return myro.globvars.robot.getObstacle(position)
    else:
        raise AttributeError("need to initialize robot")
    
def setIRPower(value):
    if myro.globvars.robot:
        return myro.globvars.robot.setIRPower(value)
    else:
        raise AttributeError("need to initialize robot")

def getBattery():
    if myro.globvars.robot:
        return myro.globvars.robot.getBattery()
    else:
        raise AttributeError("need to initialize robot")

def identifyRobot():
    if myro.globvars.robot:
        return myro.globvars.robot.identifyRobot()
    else:
        raise AttributeError("need to initialize robot")

def getIRMessage():
    if myro.globvars.robot:
        return myro.globvars.robot.getIRMessage()
    else:
        raise AttributeError("need to initialize robot")

def sendIRMessage(msg):
    if myro.globvars.robot:
        return myro.globvars.robot.sendIRMessage(msg)
    else:
        raise AttributeError("need to initialize robot")

def setCommunicateLeft(on=True):
    if myro.globvars.robot:
        return myro.globvars.robot.setCommunicateLeft(on)
    else:
        raise AttributeError("need to initialize robot")

def setCommunicateRight(on=True):
    if myro.globvars.robot:
        return myro.globvars.robot.setCommunicateLeft(on)
    else:
        raise AttributeError("need to initialize robot")

def setCommunicateCenter(on=True):
    if myro.globvars.robot:
        return myro.globvars.robot.setCommunicateCenter(on)
    else:
        raise AttributeError("need to initialize robot")

def setCommunicateAll(on=True):
    if myro.globvars.robot:
        return myro.globvars.robot.setCommunicateAll(on)
    else:
        raise AttributeError("need to initialize robot")

def configureBlob(y_low=0, y_high=255,
                  u_low=0, u_high=255,
                  v_low=0, v_high=255,
                  smooth_thresh=4):
    if myro.globvars.robot:
        return myro.globvars.robot.configureBlob(y_low, y_high, u_low, u_high, v_low, v_high, smooth_thresh)
    else:
        raise AttributeError("need to initialize robot")
    
def setWhiteBalance(value):
    if myro.globvars.robot:
        return myro.globvars.robot.setWhiteBalance(value)
    else:
        raise AttributeError("need to initialize robot")

def darkenCamera(value=0):
    if myro.globvars.robot:
        return myro.globvars.robot.darkenCamera(value)
    else:
        raise AttributeError("need to initialize robot")

def manualCamera(gain=0x00, brightness=0x80, exposure=0x41):
    if myro.globvars.robot:
        return myro.globvars.robot.manualCamera(gain, brightness, exposure)
    else:
        raise AttributeError("need to initialize robot")

def autoCamera(value=0):
    if myro.globvars.robot:
        return myro.globvars.robot.autoCamera()
    else:
        raise AttributeError("need to initialize robot")

def setLEDFront(value):
    """ Set the Light Emitting Diode on the robot's front. """
    if myro.globvars.robot:
        return myro.globvars.robot.setLEDFront(value)
    else:
        raise AttributeError("need to initialize robot")

def setLEDBack(value):
    """ Set the Light Emitting Diode on the robot's back. """
    if myro.globvars.robot:
        return myro.globvars.robot.setLEDBack(value)
    else:
        raise AttributeError("need to initialize robot")

################ New Fluke2 functions ###############

def setPicSize(value):
    """ Set the picture size """
    if myro.globvars.robot:
        return myro.globvars.robot.setPicSize(value)
    else:
        raise AttributeError("need to initialize robot")

def servo(id, position):
    """ Commands servo number id to position position """
    if myro.globvars.robot:
        return myro.globvars.robot.servo(id, position)
    else:
        raise AttributeError("need to initialize robot")

def getFlukeLog():
    """ Downloads and prints the fluke2 error log """
    if myro.globvars.robot:
        return myro.globvars.robot.getFlukeLog()
    else:
        raise AttributeError("need to initialize robot")

def enablePanNetworking():
    """ Enables bluetooth PAN TCP/IP over bluetooth networking """
    if myro.globvars.robot:
        return myro.globvars.robot.enablePanNetworking()
    else:
        raise AttributeError("need to initialize robot")

########################### Pictures:

def _ndim(n, *args, **kwargs):
    if not args:
        return [kwargs.get("value", 0)] * n
    A = []
    for i in range(n):
        A.append( _ndim(*args, **kwargs) )
    return A

class Column(object):
    def __init__(self, picture, column):
        self.picture = picture
        self.column = column
    def __getitem__(self, row):
        return self.picture.getPixel(self.column, row)

class Array(object):
    def __init__(self, n = 0, *args, **kwargs):
        if type(n) == Picture:
            self.data = n
        else:
            self.data = _ndim(n, *args, **kwargs)
    def __len__(self):
        return len(self.data)

    def __getitem__(self, *args):
        if type(self.data) == Picture:
            return Column(self.data, args[0])
        else:
            current = self.data
            for i in args:
                n, rest = args[0], args[1:]
                current = current[n]
            return current

def makeArray(*args, **kwargs):
    """ Returns an array of the given dimensions. """
    return Array(*args, **kwargs)

def takePicture(mode=None):
    """ Takes a picture using the camera. Mode can be 'color', 'gray', or 'blob' """
    if myro.globvars.robot:
        return myro.globvars.robot.takePicture(mode)
    else:
        raise AttributeError("need to initialize robot")

def loadPicture(filename):
    """ Loads a picture from a filename. """
    picture = Picture()
    picture.load(filename)
    return picture

def copyPicture(picture):
    """ Takes a Picture object and returns a copy. """
    newPicture = Picture()
    newPicture.set(getWidth(picture), getHeight(picture),
                   picture.image, mode = "image")
    return newPicture

def makePicture(*args):
    """
    Takes zero or more args to make a picture.

    makePicture() - makes a 0x0 image
    makePicture(width, height)
    makePicture("filename")
    makePicture("http://image")
    makePicture(width, height, data)
    makePicture(width, height, data, "mode")
    """
    if len(args) == 0:
        retval = Picture()
    elif len(args) == 1:
        filename = args[0]
        retval = Picture()
        if filename.startswith("http://"):
            filename, message = urllib.urlretrieve(filename)
        retval.load(filename)
    elif len(args) == 2:
        x = args[0]
        y = args[1]
        retval = Picture()
        retval.set(x, y)
    elif len(args) == 3:
        x = args[0]
        y = args[1]
        if type(args[2]) in [Color, Pixel]:
            retval = Picture()
            retval.set(x, y, value=args[2].getRGB())
        elif type(args[2]) == int:
            retval = Picture()
            retval.set(x, y, value=args[2])
        elif type(args[2]) in [list, tuple]: # Undocumented
            array = args[2]
            retval = Picture()
            retval.set(x, y, value=args[2])
        else:
            raise AttributeError("unknown type: %s is '%s'; " +
                                 "should be Color, Pixel, int grayscale", 
                                 args[2], type(args[2]))
    elif len(args) == 4:
        x = args[0]
        y = args[1]
        array = args[2]
        mode = args[3]
        retval = Picture()
        retval.set(x, y, array, mode)
    return retval

def writePictureTo(picture, filename):
    return picture.image.save(filename)

def savePicture(picture, filename):
    if type(picture) == type([]):
        import ImageChops
        from GifImagePlugin import getheader, getdata
        # open output file
        fp = open(filename, "wb")
        previous = None
        for im in picture:
            if type(im) == type(""): # filename
                im = Image.open(im)
                im.load()
                im = im.convert("P") # in case jpeg, etc
            else:
                im = im.image.convert("P")
            if not previous:
                for s in getheader(im) + getdata(im):
                    fp.write(s)
            else:
                delta = ImageChops.subtract_modulo(im, previous)
                bbox = delta.getbbox()
                if bbox:
                    for s in getdata(im.crop(bbox), offset = bbox[:2]):
                        fp.write(s)
            previous = im.copy()
        fp.write(";")
        fp.close()
    else:
        return picture.image.save(filename)

def getWidth(picture):
    return picture.width

def getHeight(picture):
    return picture.height

def getPixel(picture, x, y):
    return picture.getPixel(x, y)

def getPixels(picture):
    return picture.getPixels()

def setPixel(picture, x, y, color):
    return picture.setColor(x, y, color)

def getGray(picture, x, y):
    return sum((picture.getPixel(x, y)).getRGB())/3

def setGray(picture, x, y, gray):
    return getPixel(picture, x, y).setRGB([gray,gray,gray])

############################# Pixels and Colors

def getX(pixel):
    return pixel.x

def getY(pixel):
    return pixel.y

def getRed(pixel):
    return pixel.getRGB()[0]

def getGreen(pixel):
    return pixel.getRGB()[1]

def getBlue(pixel):
    return pixel.getRGB()[2]

def getColor(pixel):
    return pixel.getColor()

def getGray(pixel):
    return sum(pixel.getRGB())/3

def setRGB(pixel_or_color, rgb):
    return pixel_or_color.setRGB(rgb)

def setRGBA(pixel_or_color, rgba):
    return pixel_or_color.setRGBA(rgba)

def getRGB(pixel_or_color):
    return pixel_or_color.getRGB()

def getRGBA(pixel_or_color):
    return pixel_or_color.getRGBA()

def setRed(pixel, value):
    return pixel.setColor(Color(value, pixel.getRGB()[1], pixel.getRGB()[2]))

def setGreen(pixel, value):
    return pixel.setColor(Color(pixel.getRGB()[0], value, pixel.getRGB()[2]))

def setBlue(pixel, value):
    return pixel.setColor(Color(pixel.getRGB()[0], pixel.getRGB()[1], value))

def setGray(pixel, value):
    return pixel.setColor(Color(value, value, value))

def setAlpha(pixel, value):
    return pixel.setAlpha(value)

def getAlpha(pixel):
    return pixel.getAlpha()

def setColor(pixel, color):
    return pixel.setColor(color)

def makeColor(red, green, blue, alpha=255):
    return Color(red, green, blue, alpha)

def makeDarker(color):
    return color.makeDarker()

def makeLighter(color):
    return color.makeLighter()

def odd(n): return (n % 2) == 1
def even(n): return (n % 2) == 0
def wall(threshold=4500): return getObstacle(1) > threshold 

def loop(*functions):
    """
    Calls each of the given functions sequentially, N times.
    Example:

    >>> loop(f1, f2, 10)
    will call f1() then f2(), 10 times.
    """
    assert len(functions) > 1,"loop: takes 1 (or more) functions and an integer"
    assert type(functions[-1]) == int, "loop: last parameter must be an integer"
    count = functions[-1]
    for i in range(count):
        for function in functions[:-1]:
            print ("   loop #%d: running %s()... " % (i + 1, function.__name__), end="")
            try:
                retval = function()
            except TypeError:
                retval = function(i + 1)
            if retval:
                print (" => %s" % retval)
            else:
                print ("")
    stop()
    return "ok"

def doTogether(*functions):
    """
    Runs each of the given functions at the same time.
    Example:

    >>> doTogether(f1, f2, f3)
    will call f1() f2() and f3() together.
    """
    thread_results = [None] * len(functions)
    def makeThread(function, position):
        def newfunction():
            result = function()
            thread_results[position] = result
            return result
        import threading
        thread = threading.Thread()
        thread.run = newfunction
        return thread
    assert len(functions) >= 2, "doTogether: takes 2 (or more) functions"
    thread_list = []
    # first make the threads:
    for i in range(len(functions)):
        thread_list.append(makeThread(functions[i], i))
    # now, start them:
    for thread in thread_list:
        thread.start()
    # wait for them to finish:
    for thread in thread_list:
        thread.join()
    if thread_results == [None] * len(functions):
        print ('ok')
    else:
        return thread_results

def beepScale(duration, start, stop, factor=2):
    """
    Calls computer.beep(duration, Hz) repeatedly, where Hz is between
    the given start and stop frequencies, incrementing by the given
    factor.
    """
    hz = start
    while hz <= stop:
        computer.beep(duration, hz)
        hz *= factor

def getFilenames(pattern):
    """ Get a list of filenames via a pattern, like "z??.jpg"."""
    filenames = glob.glob(pattern)
    filenames.sort() # get in order, back to front
    return filenames

# --------------------------------------------------------
# Error handler:
# --------------------------------------------------------
def _myroExceptionHandler(etype, value, tb):
    # make a window
    #win = HelpWindow()
    lines = traceback.format_exception(etype, value, tb)
    print ("Myro is stopping: -------------------------------------------",  file=sys.stderr)
    for line in lines:
        print (line.rstrip(),  file=sys.stderr)
sys.excepthook = _myroExceptionHandler

from myro.robots.scribbler import Scribbler
from myro.graphics import *

_functions = ("timer", 
              "time Remaining", 
              "set Forwardness",
              "wait",
              "current Time",
              "pick One",
              "flip Coin",
              "random Number",
              "request Stop",
              "initialize",
              "translate",
              "rotate",
              "move",
              "forward",
              "backward",
              "turn",
              "turn Left",
              "turn Right",
              "stop",
              "open Connection",
              "close Connection",
              "get",
              "get Version",
              "get Light",
              "get I R",
              "get Line",
              "get Stall",
              "get Info",
              "get All",
              "get Name",
              "get Start Song",
              "get Volume",
              "update",
              "beep",
              "set",
              "set L E D",
              "set Name",
              "set Volume",
              "set Start Song",
              "motors",
              "restart",
              "calibrate",
              "play Song",
              "play Note",
              "get Bright",
              "get Obstacle",
              "set I R Power",
              "get Battery",
              "set White Balance",
              "set L E D Front",
              "set L E D Back",
              "make Array",
              "take Picture",
              "load Picture",
              "copy Picture",
              "make Picture",
              "write Picture To",
              "save Picture",
              "get Width",
              "get Height",
              "get Pixel",
              "get Pixels",
              "set Pixel",
              "get X",
              "get Y",
              "get Red",
              "get Green",
              "get Blue",
              "get Color",
              "set Red",
              "set Green",
              "set Blue",
              "set Color",
              "make Color",
              "make Darker",
              "make Lighter",
              )

myro.globvars.makeEnvironment(locals(), _functions)
