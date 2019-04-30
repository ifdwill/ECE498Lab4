from picamera import PiCamera
from time import sleep
import time
import os
import keyboard
import sys
from time import localtime, strftime
import RPi.GPIO as GPIO
from hx711 import HX711

def cleanAndExit():
    print("Cleaning...")
    GPIO.cleanup()
    print("BYE!")
    sys.exit()
    
camera = PiCamera()
timestamp = localtime()
folderpath = strftime("/home/pi/Documents/498lab4/Photos/%m_%d_%Y/",timestamp)
hx = HX711(5,6)
hx.set_reading_format("MSB", "MSB")

hx.set_reference_unit(440) #found value 440 using calibration
hx.reset()
hx.tare()
currentWeight = 0
pictureNum = 0

while True:
    try:
        val = hx.get_weight(5)
        
        if (val - currentWeight >= 3 ): #detected a change in mail
            camera.start_preview()
            currentWeight = val
            if not os.path.exists(folderpath):
                os.mkdir(folderpath)
            camera.capture(folderpath+'image%s.jpg' % pictureNum)
            pictureNum += 1
            camera.stop_preview()
        print(val)    
        hx.power_down()
        hx.power_up()
        time.sleep(3)
        
        if (val - currentWeight) < 0:
            #reset the weight
            currentWeight = 0
        
    except(KeyboardInterrupt, SystemExit):
        cleanAndExit()