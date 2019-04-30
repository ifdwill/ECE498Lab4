import os
import time
from time import localtime, strftime

timestamp = localtime()
folderpath = strftime("/home/pi/Documents/498lab4/Photos/%m_%d_%Y/",timestamp)

print(sorted(os.listdir(folderpath)))