import time
from time import localtime, strftime

currtime = strftime("Mail Received on: %B %d %Y at %I:%M %p", localtime())
print(currtime)