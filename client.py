import datetime
import getpass
import hashlib
import json
import pprint
import socket
import string
import sys
import thread
import time



# Client Variable
LOG = True
listening = 0
listenerblocker = 0
print("\n\nMini Facebook Client")
# host = "localhost:" + str(int(sys.argv[1]))
host = raw_input("Enter the Mini Facebook server [IPv4]:[PORT] : ")
port = int(host.split(":")[1])
host = host.split(":")[0]

# Assistant Function

# MiniFacebookProtocal_decode
def mfp_decode(data):
    try:
        return json.loads(data)
    except:
        print("ERROR:")
        print(data)
        print("is not a valid JSON")
# MiniFacebookProtocal_encode
def mfp_encode(request, data):
    data = {
        "request"   :   request,
        "data"      :   data,
    }
    try:
        return json.dumps(data)
    except:
        print("Error:")
        print(data)
        print("cannot be encoded to JSON")

def logprint(text):
    if (LOG):
        print(text)

def logpprint(text):
    if (LOG):
        pprint.pprint(text, width=1)

def timetostr(timestamp):
    return datetime.datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')




"""
          oooo   o8o                            .   oooooooooooo                                   
          `888   `"'                          .o8   `888'     `8                                   
 .ooooo.   888  oooo   .ooooo.  ooo. .oo.   .o888oo  888         oooo  oooo  ooo. .oo.    .ooooo.  
d88' `"Y8  888  `888  d88' `88b `888P"Y88b    888    888oooo8    `888  `888  `888P"Y88b  d88' `"Y8 
888        888   888  888ooo888  888   888    888    888    "     888   888   888   888  888       
888   .o8  888   888  888    .o  888   888    888 .  888          888   888   888   888  888   .o8 
`Y8bod8P' o888o o888o `Y8bod8P' o888o o888o   "888" o888o         `V88V"V8P' o888o o888o `Y8bod8P' 
"""


def login():
    # welcome message
    welcome = mfp_decode(conn.recv(1024))
    print(welcome['data'])
    ulogincred = {}
    ulogincred['username'] = raw_input("Login: ")
    if (ulogincred['username'] == "!exit"):
        print("Exiting..")
        data = {
            "username"  :   "exit",
            "password"  :   ""
        }
        data = mfp_encode("login", data)
        logpprint(data)
        conn.sendall(data)
        time.sleep(0.5)
        # conn.close()
        sys.exit()
    # Ghost typing password and Encrypt password
    ulogincred['password'] = hashlib.md5(getpass.getpass()).hexdigest()
    # Encode loginCred to JSON
    ulogincred = mfp_encode("login", ulogincred)
    logpprint(ulogincred)
    # Submit JSON
    logprint("Sending ulogincred")
    conn.sendall(ulogincred)
    # Check login result
    result = conn.recv(1024)
    result = mfp_decode(result)
    if (result["respond"] == "login"):
        if (result["success"] == 1):
            print("Last login: " + timetostr(result['data']['lastlogin']))
            return result['data']

        else:
            print("Login failed: " + result['data'])
            return 0
    else:
        return 0


def changepwd():
    password = {}
    print("Enter your OLD password:")
    password['oldpwd'] = hashlib.md5(getpass.getpass()).hexdigest()
    print("Enter your NEW password:")
    password['newpwd1'] = hashlib.md5(getpass.getpass()).hexdigest()
    print("Enter your NEW password again:")
    password['newpwd2'] = hashlib.md5(getpass.getpass()).hexdigest()
    
    msg = mfp_encode("chpwd", password)
    logprint(msg)
    conn.sendall(msg)


def messenger():
    logprint("Entered messenger mode")
    target = ""
    while True:
        while (target == ""):
            print("You may change your chat target at any time with /to [username]")
            target = raw_input("Who do you want to chat with? ")
        msg = raw_input("To "+target+" : ")
        if (msg.split(" ")[0] == "/to"):
            target = msg.split(" ")[1]
            print("Changing chat target username to " + target)
        elif (msg == "!exit"):
            logprint("Returning to idle mode")
            return
        else:
            msg = {
                "username"  :   target,
                "body"      :   msg,
            }
            msg = mfp_encode("msg", msg)
            logprint(msg)
            conn.sendall(msg)


def procfr():
    global listenerblocker
    logprint("Entered procfr mode")
    msg = mfp_encode("procfr", "")
    listenerblocker = 1
    conn.settimeout(None)
    conn.sendall(msg)
    while True:
        fr = conn.recv(1024)
        fr = mfp_decode(fr)
        if (fr['respond'] == "procfr"):
            if (fr['success'] == 0):
                listenerblocker = 0
                return
            agree = ""
            while ((agree != "Y") and (agree != "N")):
                agree = raw_input(fr['data'] + " has requested to be your friend. Agree? (Y/N): ")
            agree = {
                "username"  :   fr['data'],
                "agree"     :   agree
            }
            agree = mfp_encode("procfr", agree)
            conn.sendall(agree)


def newstatus():
    logprint("Entered newstatus mode")
    # title = raw_input("Title: ")
    body = raw_input("Status: ")
    msg = mfp_encode("newstatus", body)
    logprint(msg)
    conn.sendall(msg)













"""
oooo   o8o               .                                            
`888   `"'             .o8                                            
 888  oooo   .oooo.o .o888oo  .ooooo.  ooo. .oo.    .ooooo.  oooo d8b 
 888  `888  d88(  "8   888   d88' `88b `888P"Y88b  d88' `88b `888""8P 
 888   888  `"Y88b.    888   888ooo888  888   888  888ooo888  888     
 888   888  o.  )88b   888 . 888    .o  888   888  888    .o  888     
o888o o888o 8""888P'   "888" `Y8bod8P' o888o o888o `Y8bod8P' d888b    
"""

def listener():
    global listening
    global conn
    listening = 1

    logprint("Listener thread started")
    while (user!=0):
        while(listenerblocker):
            pass
        conn.settimeout(0.2)
        try:
            data = conn.recv(1024)
        except:
            continue
        data = mfp_decode(data)
        logpprint(data)

        if (data['respond'] == "feeds"):
            if (data['success'] == 1):
                for post in data['data']:
                    print("\n================================")
                    print("PostID:" + str(post['postid']) + "\tSendtime: " + timetostr(post['sendtime']))
                    print("New Status from " + post['username'])
                    print("\t"+post['body'])
                    print("Likes: " + str(post['likes']))
                    print("Comments:")
                    comments = json.loads(post['comments'])
                    for c in comments:
                        print("\t" + c[0] + ": " + c[1])
                    # pprint.pprint(post['comments'])
                    print("\n")
            else:
                print(data['data'])

        elif (data['respond'] == "menu"):
            for item in data['data']:
                print("{:>12}    {:>12}".format(item, data['data'][item]))
        
        elif (data['respond'] == "msg"):
            print("[" + timetostr(data['data']['sendtime']) + "] " + data['data']['username'] + " : " + data['data']['body'])
        
        elif (data['respond'] == "viewf"):
            for i in data['data']:
                print(i)

        else:
            print(data['data'])
    
    conn.settimeout(None)
    listening = 0
    logprint("Listener thread stopped")













"""
 .oooooo..o               .                          
d8P'    `Y8             .o8                          
Y88bo.       .ooooo.  .o888oo oooo  oooo  oo.ooooo.  
 `"Y8888o.  d88' `88b   888   `888  `888   888' `88b 
     `"Y88b 888ooo888   888    888   888   888   888 
oo     .d8P 888    .o   888 .  888   888   888   888 
8""88888P'  `Y8bod8P'   "888"  `V88V"V8P'  888bod8P' 
                                           888       
                                          o888o      
"""
# Establish connection
conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    conn.connect((host, port))
except socket.error , msg:
    print '\tERROR: Connection Failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()



"""
 .oooooo..o                              o8o                        
d8P'    `Y8                              `"'                        
Y88bo.       .ooooo.   .oooo.o  .oooo.o oooo   .ooooo.  ooo. .oo.   
 `"Y8888o.  d88' `88b d88(  "8 d88(  "8 `888  d88' `88b `888P"Y88b  
     `"Y88b 888ooo888 `"Y88b.  `"Y88b.   888  888   888  888   888  
oo     .d8P 888    .o o.  )88b o.  )88b  888  888   888  888   888  
8""88888P'  `Y8bod8P' 8""888P' 8""888P' o888o `Y8bod8P' o888o o888o 
"""
user = 0
while True:
    # Check user login status
    while (user == 0):
        user = login()

    if (listening == 0):
        logprint("Logged in, starting listener")
        thread.start_new_thread(listener, ())
    
    print("Welcome, "+ user['username'] + ", type !menu for all available commands")
    msg = raw_input()
    
    # ADD FRIEND
    if (msg == "!add"):
        addname = raw_input("Who do you want to add? ")
        logprint("Request to add friend: " + addname)
        msg = { "username" : addname }
        msg = mfp_encode("addf", msg)
        conn.sendall(msg)

    # CHANGEPWD
    elif (msg == "!changepwd"):
        changepwd()

    # COMMENTS
    elif (msg == "!comments"):
        data = {
            "pid"   :   "empty",
            "body"  :   "",
        }
        while (not data['pid'].isdigit()):
            data['pid'] = raw_input("Which postid do you want to comment? ")
        data['body'] = raw_input("What do you want to comment? ")
        msg = mfp_encode("comments", data)
        conn.sendall(msg)

    # FEEDS
    elif (msg == "!feeds"):
        msg = mfp_encode("feeds", "")
        conn.sendall(msg)
    
    # LIKES
    elif (msg == "!likes"):
        pid = "empty"
        while (not pid.isdigit()):
            pid = raw_input("Which postid do you like? ")
        msg = mfp_encode("likes", pid)
        conn.sendall(msg)

    # LOGOUT
    elif (msg == "!logout"):
        msg = mfp_encode("logout", "")
        user = 0
        conn.sendall(msg)
        conn.settimeout(None)
        result = conn.recv(1024)

    # MENU
    elif (msg == "!menu"):
        msg = mfp_encode("menu", "")
        conn.sendall(msg)

    # MESSENGER
    elif (msg == "!msg"):
        messenger()

    # VERBOSE
    elif (msg == "!verbose"):
        LOG = not LOG
        print("Verbose: " + str(LOG))

    # NEW STATUS
    elif (msg == "!newstatus"):
        newstatus()

    # PROCESS FRIEND REQUEST
    elif (msg == "!procfr"):
        procfr()

    # SVERBOSE
    elif (msg == "!sverbose"):
        msg = mfp_encode("sverbose", "")
        conn.sendall(msg)

    # VIEW FRIEND LIST
    elif (msg == "!friends"):
        msg = mfp_encode("viewf", "")
        conn.sendall(msg)

    # WALL
    elif (msg == "!wall"):
        targetuid = raw_input("Whose posts do you want to see? (username) ")
        msg = mfp_encode("wall", targetuid)
        conn.sendall(msg)

    # default
    else:
        msg = mfp_encode("", msg)
        conn.sendall(msg)

    time.sleep(0.5)

