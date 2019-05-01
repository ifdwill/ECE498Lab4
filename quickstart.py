from __future__ import print_function
import pickle
import os.path
import time
from time import localtime, strftime, sleep
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from picamera import PiCamera
import os
import mimetypes
import base64
import sys
from apiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import keyboard
import RPi.GPIO as GPIO
from hx711 import HX711
import shutil

def cleanAndExit():
    #clean and exit function for gpio stuff
    print("Cleaning...")
    GPIO.cleanup()
    print("BYE!")
    sys.exit()

# If modifying these scopes, delete the file token.pickle.
#SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SCOPES = ['https://mail.google.com/']

def create_message(sender, to, subject, message_text):
    """
    Creates a message with just text
    """
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    return {'raw': base64.urlsafe_b64encode(message.as_string())}

def create_draft(service, user_id, message_body):
    """
    Creates a draft from a message
    """
    message = {'message':message_body}
    draft = service.users().drafts().create(userId = user_id, body = message).execute()        
    print('Draft id: %s\nDraft message: %s' % (draft['id'], draft['message']))
    return draft
    
def create_message_with_attachment(sender, to, subject, message_text, file):
    """
    Creates a message with a single attachment
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    
    msg = MIMEText(message_text)
    message.attach(msg)
    
    content_type, encoding = mimetypes.guess_type(file)
    
    if content_type is None or encoding is not None:
        content_type = 'application/octet-stream'
    main_type, sub_type = content_type.split('/', 1)
    
    if main_type == 'image':
        fp = open(file, 'rb')
        msg = MIMEImage(fp.read(), _subtype = sub_type)
        fp.close()
    else:
        fp = open(file, 'rb')
        msg = MIMEBase(main_type, sub_type)
        msg.set_payload(fp.read())
        fp.close()
    filename = os.path.basename(file)
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    message.attach(msg)
    
    return {'raw': base64.urlsafe_b64encode(message.as_string())}

def create_message_with_multi_attachment(sender, to, subject, message_text, folderpath, startnum, endnum):
    """
    Creates a message with multiple attachments from a folder path
    """
    message = MIMEMultipart()
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    file = sorted(os.listdir(folderpath))
    msg = MIMEText(message_text)
    message.attach(msg)
    #for i in range(len(file)):
    for i in range(endnum-startnum):
        content_type, encoding = mimetypes.guess_type(file[startnum + i])
    
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
    
        if main_type == 'image':
            fp = open(folderpath+file[startnum+i], 'rb')
            msg = MIMEImage(fp.read(), _subtype = sub_type)
            fp.close()
        else:
            fp = open(folderpath+file[i], 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(folderpath+file[startnum+i])
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)
    
    return {'raw': base64.urlsafe_b64encode(message.as_string())}
def delete_old_folders():
    """
    Deletes old images from folder after a certain amount of time
    """
    timestamp = localtime()
    curr_month = int(strftime("%m", timestamp))
    if curr_month == 1:
        prev_month = 12
    else:
        prev_month = curr_month-1
    date_to_delete = strftime(str(prev_month) + "_" + "%d_%Y", timestamp)
    folderpath = "/home/pi/Documents/498lab4/Photos/" + date_to_delete
    shutil.rmtree(folderpath, ignore_errors = True)
    
def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    #GPIO.cleanup()
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    #initializes the Camera
    camera = PiCamera()

    #initialize the hx711
    hx = HX711(5,6)
    hx.set_reading_format("MSB", "MSB")

    hx.set_reference_unit(440) #found through calibration
    hx.reset()
    hx.tare()
    currentWeight = 0
    pictureNum = 0
    cachetime = False
    falsePositive = False
    batchNum = 0
    
    print("Starting polling")
    while True:
        print("Start of loop")
        if cachetime == False :
            dayEndtime = time.time() + 60*60*24 # 1 day from now
            cachetime = True
            print("Set Clear time to ", dayEndtime)
        try: 
            val = hx.get_weight(5)
            if val < 0 :
                hx.reset()
                hx.tare()
            if (val - currentWeight >= 5): #something larger than 3 grams added
                timeout = time.time() + 60 # 1 minute from now
                print("New item detected, 1 minute for pictures")
                while time.time() < timeout:
                    val = hx.get_weight(5)
                    if val - currentWeight < -3 or val <= 0 : #false positive
                        print("False positive!")
                        falsePositive = True
                        break
                    if val-currentWeight >=4:
                        camera.start_preview()
                        currentWeight = val
                        folderpath = strftime("/home/pi/Documents/498lab4/Photos/%m_%d_%Y/",localtime())
                        if not os.path.exists(folderpath):
                            os.mkdir(folderpath)
                        camera.capture(folderpath +'image%s.jpg' % pictureNum)
                        pictureNum += 1
                        camera.stop_preview()
                    print(val)
                    hx.power_down()
                    hx.power_up()
                    time.sleep(1)
                if not falsePositive :
                    callGmailAPI(service, pictureNum)
                falsePositive = False
                print("got here 1")
                print("current weight ", currentWeight)
                print("val", val)
                
            if (val-currentWeight < -3 ) : #something taken out
                print("sleeping")
                for i in range(10):
                    time.sleep(1)
                    print("sleep", i)
                    
                #time.sleep(30) #sleep for 30 seconds
                hx.reset()
                hx.tare()
                val = hx.get_weight(5)
                currentWeight = hx.get_weight(5)
                print("done sleeping")
            if time.time() >= dayEndtime:
                cachetime = False
                delete_old_folders()
                pictureNum = 0 # reset picture number
                print("Exiting loop!")
                break
                #cleanup the pictures at the end of the day
        except(KeyboardInterrupt, SystemExit):
            cleanAndExit()

    # Call the Gmail API
def callGmailAPI(service, numpictures):
    print("sending email!")
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    sender = "me"
    to = "smartmailbox498@gmail.com, tis.william@gmail.com"
    #to = "smartmailbox498@gmail.com, tis.william@gmail.com, atin.ganti@gmail.com"
    timestamp = localtime()
    
    subject = strftime("Mail Received on: %B %d %Y at %I:%M %p", timestamp)
    message_text = strftime("This is the mail received %B %d %Y at %I:%M %p", timestamp)
    message_text += "\nThis is an automated email sent by SMART MAILBOX"
    
    folderpath = strftime("/home/pi/Documents/498lab4/Photos/%m_%d_%Y/",timestamp)
   
    #file = folderpath+'image1.jpg'
    user_id = "smartmailbox498@gmail.com"
    #msg = create_message(sender, to, subject, message_text)
    #msg = create_message_with_attachment(sender, to, subject, message_text, file)
    if numpictures > 4 :
        for i in range(numpictures/4): 
            msg = create_message_with_multi_attachment(sender, to, subject, message_text, folderpath, (i*4), (i*4) + 4)
            draft = create_draft(service, user_id, msg)
            sent = service.users().drafts().send(userId = user_id, body = {'id':str(draft["id"])}).execute()
            print(sent)
    #for i in range(numpictures / 4) : # four pictures per email
    else:    
        msg = create_message_with_multi_attachment(sender, to, subject, message_text, folderpath, 0, numpictures)
        draft = create_draft(service, user_id, msg)
    
        sent = service.users().drafts().send(userId = user_id, body = {'id':str(draft["id"])}).execute()
        print(sent)
    """
    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])
    """

if __name__ == '__main__':
    main()