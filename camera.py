from picamera import PiCamera
from time import sleep
import time
import os
import keyboard
from time import localtime, strftime

camera = PiCamera()
timestamp = localtime()
folderpath = strftime("/home/pi/Documents/498lab4/Photos/%m_%d_%Y/",timestamp)
camera.start_preview()
for i in range(5): #make dynamic
    sleep(2)
    if not os.path.exists(folderpath):
        os.mkdir(folderpath)
    camera.capture(folderpath+'image%s.jpg' % i)
camera.stop_preview()