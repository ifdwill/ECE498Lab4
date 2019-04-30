from __future__ import print_function
import pickle
import os.path
import time
from time import localtime, strftime
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
import os
import mimetypes
import base64
from apiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

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

def create_message_with_multi_attachment(sender, to, subject, message_text, folderpath):
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
    for i in range(len(file)):
        content_type, encoding = mimetypes.guess_type(file[i])
    
        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
    
        if main_type == 'image':
            fp = open(folderpath+file[i], 'rb')
            msg = MIMEImage(fp.read(), _subtype = sub_type)
            fp.close()
        else:
            fp = open(folderpath+file[i], 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(folderpath+file[i])
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)
    
    return {'raw': base64.urlsafe_b64encode(message.as_string())}

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
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

    # Call the Gmail API
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
    msg = create_message_with_multi_attachment(sender, to, subject, message_text, folderpath)
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