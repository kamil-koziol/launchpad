#!/usr/bin/env python
#
# A Novation Launchpad control suite for Python.
#
# https://github.com/FMMT666/launchpad.py
#
# FMMT666(ASkr) 01/2013..09/2019..08/2020..05/2021
# www.askrprojects.net
#
#
#
#  >>>
#  >>> NOTICE FOR SPACE USERS:
#  >>>
#  >>>  Yep, this one uses tabs. Tabs everywhere.
#  >>>  Deal with it :-)
#  >>>
#

import string
import random
import sys
import array

from pygame import midi
from pygame import time


try:
    from launchpad_py.charset import *
except ImportError:
    try:
        from charset import *
    except ImportError:
        sys.exit("error loading Launchpad charset")


##########################################################################################
# CLASS Midi
# Midi singleton wrapper
##########################################################################################
class Midi:

    # instance created
    instanceMidi = None

    # ---------------------------------------------------------------------------------------
    #-- init
    # -- Allow only one instance to be created
    # ---------------------------------------------------------------------------------------
    def __init__(self):
        if Midi.instanceMidi is None:
            try:
                Midi.instanceMidi = Midi.__Midi()
            except:
                # TODO: maybe sth like sys.exit()?
                print("unable to initialize MIDI")
                Midi.instanceMidi = None

        self.devIn = None
        self.devOut = None

    # ---------------------------------------------------------------------------------------
    #-- getattr
    # -- Pass all unknown method calls to the inner Midi class __Midi()
    # ---------------------------------------------------------------------------------------
    def __getattr__(self, name):
        return getattr(self.instanceMidi, name)

    # -------------------------------------------------------------------------------------
    # --
    # -------------------------------------------------------------------------------------
    def OpenOutput(self, midi_id):
        if self.devOut is None:
            try:
                # PyGame's default size of the buffer is 4096.
                # Removed code to tune that...
                self.devOut = midi.Output(midi_id, 0)
            except:
                self.devOut = None
                return False
        return True

    # -------------------------------------------------------------------------------------
    # --
    # -------------------------------------------------------------------------------------
    def CloseOutput(self):
        if self.devOut is not None:
            # self.devOut.close()
            del self.devOut
            self.devOut = None

    # -------------------------------------------------------------------------------------
    # --
    # -------------------------------------------------------------------------------------
    def OpenInput(self, midi_id, bufferSize=None):
        if self.devIn is None:
            try:
                # PyGame's default size of the buffer is 4096.
                if bufferSize is None:
                    self.devIn = midi.Input(midi_id)
                else:
                    # for experiments...
                    self.devIn = midi.Input(midi_id, bufferSize)
            except:
                self.devIn = None
                return False
        return True

    # -------------------------------------------------------------------------------------
    # --
    # -------------------------------------------------------------------------------------
    def CloseInput(self):
        if self.devIn is not None:
            # self.devIn.close()
            del self.devIn
            self.devIn = None

    # -------------------------------------------------------------------------------------
    # --
    # -------------------------------------------------------------------------------------
    def ReadCheck(self):
        return self.devIn.poll()

    # -------------------------------------------------------------------------------------
    # --
    # -------------------------------------------------------------------------------------
    def ReadRaw(self):
        return self.devIn.read(1)

    # -------------------------------------------------------------------------------------
    # -- sends a single, short message
    # -------------------------------------------------------------------------------------
    def RawWrite(self, stat, dat1, dat2):
        self.devOut.write_short(stat, dat1, dat2)

    # -------------------------------------------------------------------------------------
    # -- Sends a list of messages. If timestamp is 0, it is ignored.
    # -- Amount of <dat> bytes is arbitrary.
    # -- [ [ [stat, <dat1>, <dat2>, <dat3>], timestamp ],  [...], ... ]
    # -- <datN> fields are optional
    # -------------------------------------------------------------------------------------
    def RawWriteMulti(self, lstMessages):
        self.devOut.write(lstMessages)

    # -------------------------------------------------------------------------------------
    # -- Sends a single system-exclusive message, given by list <lstMessage>
    # -- The start (0xF0) and end bytes (0xF7) are added automatically.
    # -- [ <dat1>, <dat2>, ..., <datN> ]
    # -- Timestamp is not supported and will be sent as '0' (for now)
    # -------------------------------------------------------------------------------------
    def RawWriteSysEx(self, lstMessage, timeStamp=0):
        # There's a bug in PyGame's (Python 3) list-type message handling, so as a workaround,
        # we'll use the string-type message instead...
        # self.devOut.write_sys_ex( timeStamp, [0xf0] + lstMessage + [0xf7] ) # old Python 2

        # array.tostring() deprecated in 3.9; quickfix ahead
        try:
            self.devOut.write_sys_ex(timeStamp, array.array(
                'B', [0xf0] + lstMessage + [0xf7]).tostring())
        except:
            self.devOut.write_sys_ex(timeStamp, array.array(
                'B', [0xf0] + lstMessage + [0xf7]).tobytes())

    ########################################################################################
    # CLASS __Midi
    # The rest of the Midi class, non Midi-device specific.
    ########################################################################################

    class __Midi:

        # -------------------------------------------------------------------------------------
        #-- init
        # -------------------------------------------------------------------------------------
        def __init__(self):
            # exception handling moved up to Midi()
            midi.init()
            # but I can't remember why I put this one in here...
            midi.get_count()

        # -------------------------------------------------------------------------------------
        # -- del
        # -- This will never be executed, because no one knows, how many Launchpad instances
        # -- exist(ed) until we start to count them...
        # -------------------------------------------------------------------------------------
        def __del__(self):
            # midi.quit()
            pass

        # -------------------------------------------------------------------------------------
        # -- Returns a list of devices that matches the string 'name' and has in- or outputs.
        # -------------------------------------------------------------------------------------
        def SearchDevices(self, name, output=True, input=True, quiet=True):
            ret = []
            i = 0

            for n in range(midi.get_count()):
                md = midi.get_device_info(n)
                if str(md[1].lower()).find(name.lower()) >= 0:
                    if quiet == False:
                        print('%2d' % (i), md)
                        sys.stdout.flush()
                    if output == True and md[3] > 0:
                        ret.append(i)
                    if input == True and md[2] > 0:
                        ret.append(i)
                i += 1

            return ret

        # -------------------------------------------------------------------------------------
        # -- Returns the first device that matches the string 'name'.
        # -- NEW2015/02: added number argument to pick from several devices (if available)
        # -------------------------------------------------------------------------------------
        def SearchDevice(self, name, output=True, input=True, number=0):
            ret = self.SearchDevices(name, output, input)

            if number < 0 or number >= len(ret):
                return None

            return ret[number]

        # -------------------------------------------------------------------------------------
        # -- Return MIDI time
        # -------------------------------------------------------------------------------------
        def GetTime(self):
            return midi.time()


########################################################################################
# CLASS LaunchpadBase
###
########################################################################################
class LaunchpadBase(object):

    def __init__(self):
        self.midi = Midi()  # midi interface instance (singleton)
        self.idOut = None   # midi id for output
        self.idIn = None   # midi id for input

        # scroll directions
        self.SCROLL_NONE = 0
        self.SCROLL_LEFT = -1
        self.SCROLL_RIGHT = 1

    # LOL; That fixes a years old bug. Officially an idiot now :)
#	def __delete__( self ):
    def __del__(self):
        self.Close()

    # -------------------------------------------------------------------------------------
    # -- Opens one of the attached Launchpad MIDI devices.
    # -------------------------------------------------------------------------------------
    def Open(self, number=0, name="Launchpad"):
        self.idOut = self.midi.SearchDevice(name, True, False, number=number)
        self.idIn = self.midi.SearchDevice(name, False, True, number=number)

        if self.idOut is None or self.idIn is None:
            return False

        if self.midi.OpenOutput(self.idOut) == False:
            return False

        return self.midi.OpenInput(self.idIn)

    # -------------------------------------------------------------------------------------
    # -- Checks if a device exists, but does not open it.
    # -- Does not check whether a device is in use or other, strange things...
    # -------------------------------------------------------------------------------------
    def Check(self, number=0, name="Launchpad"):
        self.idOut = self.midi.SearchDevice(name, True, False, number=number)
        self.idIn = self.midi.SearchDevice(name, False, True, number=number)

        if self.idOut is None or self.idIn is None:
            return False

        return True

    # -------------------------------------------------------------------------------------
    # -- Closes this device
    # -------------------------------------------------------------------------------------
    def Close(self):
        self.midi.CloseInput()
        self.midi.CloseOutput()

    # -------------------------------------------------------------------------------------
    # -- prints a list of all devices to the console (for debug)
    # -------------------------------------------------------------------------------------
    def ListAll(self, searchString=''):
        self.midi.SearchDevices(searchString, True, True, False)

    # -------------------------------------------------------------------------------------
    # -- Clears the button buffer (The Launchpads remember everything...)
    # -- Because of empty reads (timeouts), there's nothing more we can do here, but
    # -- repeat the polls and wait a little...
    # -------------------------------------------------------------------------------------
    def ButtonFlush(self):
        doReads = 0
        # wait for that amount of consecutive read fails to exit
        while doReads < 3:
            if self.midi.ReadCheck():
                doReads = 0
                self.midi.ReadRaw()
            else:
                doReads += 1
                time.wait(5)

    # -------------------------------------------------------------------------------------
    # -- Returns a list of all MIDI events, empty list if nothing happened.
    # -- Useful for debugging or checking new devices.
    # -------------------------------------------------------------------------------------
    def EventRaw(self):
        if self.midi.ReadCheck():
            return self.midi.ReadRaw()
        else:
            return []


########################################################################################
# CLASS Launchpad
###
# For 2-color Launchpads with 8x8 matrix and 2x8 top/right rows
########################################################################################
class Launchpad(LaunchpadBase):

    # LED AND BUTTON NUMBERS IN RAW MODE (DEC):
    #
    # +---+---+---+---+---+---+---+---+
    # |200|201|202|203|204|205|206|207| < AUTOMAP BUTTON CODES;
    # +---+---+---+---+---+---+---+---+   Or use LedCtrlAutomap() for LEDs (alt. args)
    #
    # +---+---+---+---+---+---+---+---+  +---+
    # |  0|...|   |   |   |   |   |  7|  |  8|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 16|...|   |   |   |   |   | 23|  | 24|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 32|...|   |   |   |   |   | 39|  | 40|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 48|...|   |   |   |   |   | 55|  | 56|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 64|...|   |   |   |   |   | 71|  | 72|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 80|...|   |   |   |   |   | 87|  | 88|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 96|...|   |   |   |   |   |103|  |104|
    # +---+---+---+---+---+---+---+---+  +---+
    # |112|...|   |   |   |   |   |119|  |120|
    # +---+---+---+---+---+---+---+---+  +---+
    #
    #
    # LED AND BUTTON NUMBERS IN XY MODE (X/Y)
    #
    #   0   1   2   3   4   5   6   7      8
    # +---+---+---+---+---+---+---+---+
    # |   |1/0|   |   |   |   |   |   |         0
    # +---+---+---+---+---+---+---+---+
    #
    # +---+---+---+---+---+---+---+---+  +---+
    # |0/1|   |   |   |   |   |   |   |  |   |  1
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  2
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |5/3|   |   |  |   |  3
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  4
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  5
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |4/6|   |   |   |  |   |  6
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  7
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |8/8|  8
    # +---+---+---+---+---+---+---+---+  +---+
    #

    # -------------------------------------------------------------------------------------
    # -- reset the Launchpad
    # -- Turns off all LEDs
    # -------------------------------------------------------------------------------------
    def Reset(self):
        self.midi.RawWrite(176, 0, 0)

    # -------------------------------------------------------------------------------------
    # -- Returns a Launchpad compatible "color code byte"
    # -- NOTE: In here, number is 0..7 (left..right)
    # -------------------------------------------------------------------------------------
    def LedGetColor(self, red, green):
        led = 0

        red = min(int(red), 3)  # make int and limit to <=3
        red = max(red, 0)      # no negative numbers

        green = min(int(green), 3)  # make int and limit to <=3
        green = max(green, 0)      # no negative numbers

        led |= red
        led |= green << 4

        return led

    # -------------------------------------------------------------------------------------
    # -- Controls a grid LED by its raw <number>; with <green/red> brightness: 0..3
    # -- For LED numbers, see grid description on top of class.
    # -------------------------------------------------------------------------------------
    def LedCtrlRaw(self, number, red, green):

        if number > 199:
            if number < 208:
                # 200-207
                self.LedCtrlAutomap(number - 200, red, green)
        else:
            if number < 0 or number > 120:
                return
            # 0-120
            led = self.LedGetColor(red, green)
            self.midi.RawWrite(144, number, led)

    # -------------------------------------------------------------------------------------
    # -- Controls a grid LED by its coordinates <x> and <y>  with <green/red> brightness 0..3
    # -------------------------------------------------------------------------------------
    def LedCtrlXY(self, x, y, red, green):

        if x < 0 or x > 8 or y < 0 or y > 8:
            return

        if y == 0:
            self.LedCtrlAutomap(x, red, green)

        else:
            self.LedCtrlRaw(((y-1) << 4) | x, red, green)

    # -------------------------------------------------------------------------------------
    # -- Sends a list of consecutive, special color values to the Launchpad.
    # -- Only requires (less than) half of the commands to update all buttons.
    # -- [ LED1, LED2, LED3, ... LED80 ]
    # -- First, the 8x8 matrix is updated, left to right, top to bottom.
    # -- Afterwards, the algorithm continues with the rightmost buttons and the
    # -- top "automap" buttons.
    # -- LEDn color format: 00gg00rr <- 2 bits green, 2 bits red (0..3)
    # -- Function LedGetColor() will do the coding for you...
    # -- Notice that the amount of LEDs needs to be even.
    # -- If an odd number of values is sent, the next, following LED is turned off!
    # -- REFAC2015: Device specific.
    # -------------------------------------------------------------------------------------
    def LedCtrlRawRapid(self, allLeds):
        le = len(allLeds)

        for i in range(0, le, 2):
            self.midi.RawWrite(
                146, allLeds[i], allLeds[i+1] if i+1 < le else 0)

#   This fast version does not work, because the Launchpad gets confused
#   by the timestamps...
#
#		tmsg= []
#		for i in range( 0, le, 2 ):
#			# create a message
#			msg = [ 146 ]
#			msg.append( allLeds[i] )
#			if i+1 < le:
#				msg.append( allLeds[i+1] )
#			# add it to the list
#			tmsg.append( msg )
#			# add a timestanp
#			tmsg.append( self.midi.GetTime() + i*10 )
#
#		self.midi.RawWriteMulti( [ tmsg ] )

    # -------------------------------------------------------------------------------------
    # -- "Homes" the next LedCtrlRawRapid() call, so it will start with the first LED again.
    # -------------------------------------------------------------------------------------
    def LedCtrlRawRapidHome(self):
        self.midi.RawWrite(176, 1, 0)

    # -------------------------------------------------------------------------------------
    # -- Controls an automap LED <number>; with <green/red> brightness: 0..3
    # -- NOTE: In here, number is 0..7 (left..right)
    # -------------------------------------------------------------------------------------
    def LedCtrlAutomap(self, number, red, green):

        if number < 0 or number > 7:
            return

        red = max(0, red)
        red = min(3, red)
        green = max(0, green)
        green = min(3, green)
        led = self.LedGetColor(red, green)

        self.midi.RawWrite(176, 104 + number, led)

    # -------------------------------------------------------------------------------------
    # -- all LEDs on
    # -- <colorcode> is here for backwards compatibility with the newer "Mk2" and "Pro"
    # -- classes. If it's "0", all LEDs are turned off. In all other cases turned on,
    # -- like the function name implies :-/
    # -------------------------------------------------------------------------------------
    def LedAllOn(self, colorcode=None):
        if colorcode == 0:
            self.Reset()
        else:
            self.midi.RawWrite(176, 0, 127)

    # -------------------------------------------------------------------------------------
    # -- Sends character <char> in colors <red/green> and lateral offset <offsx> (-8..8)
    # -- to the Launchpad. <offsy> does not have yet any function
    # -------------------------------------------------------------------------------------
    def LedCtrlChar(self, char, red, green, offsx=0, offsy=0):
        char = ord(char)

        if char < 0 or char > 255:
            return
        char *= 8

        for i in range(0, 8*16, 16):
            for j in range(8):
                lednum = i + j + offsx
                if lednum >= i and lednum < i + 8:
                    if CHARTAB[char] & 0x80 >> j:
                        self.LedCtrlRaw(lednum, red, green)
                    else:
                        self.LedCtrlRaw(lednum, 0, 0)
            char += 1

    # -------------------------------------------------------------------------------------
    # -- Scroll <text>, in colors specified by <red/green>, as fast as we can.
    # -- <direction> specifies: -1 to left, 0 no scroll, 1 to right
    # -- The delays were a dirty hack, but there's little to nothing one can do here.
    # -- So that's how the <waitms> parameter came into play...
    # -- NEW   12/2016: More than one char on display \o/
    # -- IDEA: variable spacing for seamless scrolling, e.g.: "__/\_"
    # -------------------------------------------------------------------------------------
    def LedCtrlString(self, text, red, green, direction=None, waitms=150):

        def limit(n, mini, maxi): return max(min(maxi, n), mini)

        if direction == self.SCROLL_LEFT:
            text += " "
            for n in range((len(text) + 1) * 8):
                if n <= len(text)*8:
                    self.LedCtrlChar(
                        text[limit((n // 16)*2, 0, len(text)-1)], red, green, 8 - n % 16)
                if n > 7:
                    self.LedCtrlChar(
                        text[limit((((n-8)//16)*2) + 1, 0, len(text)-1)], red, green, 8-(n-8) % 16)
                time.wait(waitms)
        elif direction == self.SCROLL_RIGHT:
            # TODO: Just a quick hack (screen is erased before scrolling begins).
            #       Characters at odd positions from the right (1, 3, 5), with pixels at the left,
            #       e.g. 'C' will have artifacts at the left (pixel repeated).
            text = " " + text + " "  # just to avoid artifacts on full width characters
#			for n in range( (len(text) + 1) * 8 - 1, 0, -1 ):
            for n in range((len(text) + 1) * 8 - 7, 0, -1):
                if n <= len(text)*8:
                    self.LedCtrlChar(
                        text[limit((n // 16)*2, 0, len(text)-1)], red, green, 8 - n % 16)
                if n > 7:
                    self.LedCtrlChar(
                        text[limit((((n-8)//16)*2) + 1, 0, len(text)-1)], red, green, 8-(n-8) % 16)
                time.wait(waitms)
        else:
            for i in text:
                for n in range(4):  # pseudo repetitions to compensate the timing a bit
                    self.LedCtrlChar(i, red, green)
                    time.wait(waitms)

    # -------------------------------------------------------------------------------------
    # -- Returns True if a button event was received.
    # -------------------------------------------------------------------------------------
    def ButtonChanged(self):
        return self.midi.ReadCheck()

    # -------------------------------------------------------------------------------------
    # -- Returns the raw value of the last button change as a list:
    # -- [ <button>, <True/False> ]
    # -------------------------------------------------------------------------------------
    def ButtonStateRaw(self):
        if self.midi.ReadCheck():
            a = self.midi.ReadRaw()
            return [a[0][0][1] if a[0][0][0] == 144 else a[0][0][1] + 96, True if a[0][0][2] > 0 else False]
        else:
            return []

    # -------------------------------------------------------------------------------------
    # -- Returns an x/y value of the last button change as a list:
    # -- [ <x>, <y>, <True/False> ]
    # -------------------------------------------------------------------------------------
    def ButtonStateXY(self):
        if self.midi.ReadCheck():
            a = self.midi.ReadRaw()

            if a[0][0][0] == 144:
                x = a[0][0][1] & 0x0f
                y = (a[0][0][1] & 0xf0) >> 4

                return [x, y+1, True if a[0][0][2] > 0 else False]

            elif a[0][0][0] == 176:
                return [a[0][0][1] - 104, 0, True if a[0][0][2] > 0 else False]

        return []
