
# coding: utf-8

# In[ ]:


import praw
from tqdm import tqdm
from praw.models import Message, Submission


# In[1]:


import time
import threading
import json
import datetime
from flask import Flask
import os


# In[ ]:


from firebase import firebase 

# authentication = firebase.FirebaseAuthentication('THIS_IS_MY_SECRET', 'het.thakkar809@gmail.com', extra={'id': '5sVnwbW5lwUdPsOUkWWXle1UwWF2'})
# firebase.authentication = authentication
# user = authentication.get_user()
# print(user.firebase_auth_token)

firebase = firebase.FirebaseApplication('https://complaintsapp-cfa95.firebaseio.com/', None)
#result = firebase.get('/twittercomplaints/complaint1', None)
#print(result)


# In[ ]:


already_processed = []
not_replied = []
unread_messages = []


# In[ ]:


def checkPost(post_text):
    post_text = post_text.lower()
    location = ''
    ctype = ''
    body = ''
    try:
        p1,p2,p3 = post_text.index('location'), post_text.index('type'), post_text.index('body')
    except:
        return False,-1,-1,-1
    p = [p1,p2,p3]
    p.sort()
    
    if(post_text[p[0]] == 'l'):
        location = post_text[p[0]+9:p[1]-1]
        if(post_text[p[1]] == 't'):
            ctype = post_text[p[1]+5:p[2]-1]
            body = post_text[p[2]+5:]
        else:
            body = post_text[p[1]+5:p[2]-1]
            ctype = post_text[p[2]+5:]
            
    if(post_text[p[0]] == 't'):
        ctype = post_text[p[0]+5:p[1]-1]
        if(post_text[p[1]] == 'l'):
            location = post_text[p[1]+9:p[2]-1]
            body = post_text[p[2]+5:]
        else:
            body = post_text[p[1]+5:p[2]-1]
            location = post_text[p[2]+9:]
            
    if(post_text[p[0]] == 'b'):
        body = post_text[p[0]+5:p[1]-1]
        if(post_text[p[1]] == 't'):
            ctype = post_text[p[1]+5:p[2]-1]
            location = post_text[p[2]+9:]
        else:
            location = post_text[p[1]+9:p[2]-1]
            ctype = post_text[p[2]+5:]
    
    return True,location,ctype,body
    


# In[ ]:


def handle_replies(reddit):
    while(1):
        if(not_replied):
            for i in not_replied:
                complaint_uri = '/twittercomplaints/' + str(i)
                result = firebase.get(complaint_uri, None)
                #complaint = json.loads(result)
                complaint = result
                
                if(complaint['approved'] == 'true'):
                    
                    try:
                        post = Submission(reddit, complaint['postID'])
                        post = reddit.submission(post)
                    except:
                        firebase.delete('/twittercomplaints/', str(i))
                        not_replied.remove(i)
                        continue
                    
                    post.reply('Your complaint has been accepted. For updates, go to : test.com/abc')
                    print('replied accepted')
                    not_replied.remove(i)
                    userName = post.author
                    
                elif(complaint['approved'] == 'false'):
                
                
                    try:
                        post = Submission(reddit, complaint['postID'])
                        post = reddit.submission(post)
                    except:
                        firebase.delete('/twittercomplaints/', str(i))
                        not_replied.remove(i)
                        continue
                        
                    post = Submission(reddit, complaint['postID'])
                    post = reddit.submission(post)
                    userName = post.author
                    reddit.redditor(userName.name).message('Regarding Complaint', 'Your complaint was rejected by the manager')
                    post.mod.remove()
                    not_replied.remove(i)
                    firebase.delete('/twittercomplaints/',str(i))
                    print('dm rejected')
        else:
            time.sleep(3)


# In[ ]:


global_text = ''


# In[ ]:


def handle_posts(reddit):
    subreddit = reddit.subreddit('ComplaintsApp')
    for submission in tqdm(subreddit.stream.submissions(skip_existing = True)):
        if(submission.id not in already_processed):
            already_processed.append(submission.id)
            post = reddit.submission(submission)
            title = post.title
            userName = post.author
            text = post.selftext
            
            print(post.id)
            isValid,location,ctype,body = checkPost(text)
            global_text = text
            
            print('Passing text : ' + text)
            if(isValid):
                
                print('Location from fn ' + location)
                print('Type from fn '+ ctype)
                print('Body from fn '+ body)
            
            
            if(isValid == False):
                reddit.redditor(userName.name).message('Regarding Complaint', 'Your complaint did not match the required format and was deleted. Please take a look at the required format in the community information and post again')
                post.mod.remove()
            else:
                submission.reply('Your complaint is being processed by our manager and will be responded to soon')
                putfile = {
                    'postID' : post.id,
                    'Body' : body,
                    'IssuerID' : userName.id,
                    'IssuerUsername' : userName.name,
                    'Location' : location,
                    'platform' : 'Reddit',
                    'Timestamp' : str(1000*int(datetime.datetime.now().timestamp())),
                    'Type' : ctype,
                    'cssClass' : 'is-danger',
                    'logoURL' : 'http://i.imgur.com/sdO8tAw.png',
                    'approved' : 'pending'
                    
                }
                #putfile = json.dumps(putfile)
                result = firebase.post('/twittercomplaints/', putfile )
                print(result)
                not_replied.append(result['name'])


# In[ ]:


if __name__ == '__main__':
    
    
    #app = Flask(__name__)
    #app.run(host= '0.0.0.0', port = os.environ.get('PORT'))
    c_id = os.environ['c_id']
    c_secret = os.environ['c_secret']
    r_password = os.environ['r_password']
    
    reddit = praw.Reddit(client_id = c_id,
                     client_secret = c_secret,
                     password = r_password,
                     user_agent = 'ComplaintsApp',
                     username = 'complaintBotSEN')
    
    handle_complaint = threading.Thread(target = handle_posts, args = (reddit,))
    reply_complaint = threading.Thread(target = handle_replies, args = (reddit,))
    
    handle_complaint.start()
    reply_complaint.start()
    
    reply_complaint.join()
    
    

