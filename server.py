import hashlib
import json
import pprint
import socket
import sqlite3
import string
import sys
import thread
import time




# Server Variable
LOG = True
HOST = '0.0.0.0'
# PORT = 5207
PORT = int(sys.argv[1])
activeClients = {}
SYSTEM = {
    "uid"       :   0,
    "username"  :   "SYSTEM",
}
MENU = {
    "!add"      :   "Add a friend",
    "!changepwd":   "Change your password",
    "!exit"     :   "Return to the parent mode",
    "!feeds"    :   "See if there are any friends' status updates",
    "!friends"  :   "View your friend list",
    "!likes"    :   "Like a postid",
    "!logout"   :   "Log out from current session",
    "!msg"      :   "Enter messenger mode",
    "!newstatus":   "Post a new status",
    "!procfr"   :   "Process friend requests",
    "!verbose"  :   "Toggle client verbose output",
    "!sverbose" :   "Toggle server verbose output",
    "!wall"     :   "See the timeline of a username",
}


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
def mfp_encode(respond, success, data):
    data = {
        "respond"  :   respond,
        "success"   :   success,
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


"""
                                                           oooooooooooo                                   
                                                           `888'     `8                                   
 .oooo.o  .ooooo.  oooo d8b oooo    ooo  .ooooo.  oooo d8b  888         oooo  oooo  ooo. .oo.    .ooooo.  
d88(  "8 d88' `88b `888""8P  `88.  .8'  d88' `88b `888""8P  888oooo8    `888  `888  `888P"Y88b  d88' `"Y8 
`"Y88b.  888ooo888  888       `88..8'   888ooo888  888      888    "     888   888   888   888  888       
o.  )88b 888    .o  888        `888'    888    .o  888      888          888   888   888   888  888   .o8 
8""888P' `Y8bod8P' d888b        `8'     `Y8bod8P' d888b    o888o         `V88V"V8P' o888o o888o `Y8bod8P' 
"""

def login(conn, dbconn):
    global activeClients
    db = dbconn.cursor()
    user = {}
    db_user = {}
    logprint("Sending Welcome message")
    time.sleep(0.5)
    welcome = """=============================================
    Welcome to CS164 Mini Facebook Server
    Enter !exit to exit the client"""
    welcome = mfp_encode("welcome", 1, welcome)
    conn.sendall(welcome)
    ulogincred = ""
    while (ulogincred == ""):
        ulogincred = conn.recv(1024)
    logprint("Received: "+ulogincred)
    ulogincred = mfp_decode(ulogincred)

    if (ulogincred["request"] != "login"):
        print("ERROR: unexpected client status")
        return 0

    ulogincred = ulogincred["data"]
    logprint("Client submitted login cred:")
    logpprint(ulogincred)
    # Client exit
    if (ulogincred["username"] == "exit"):
        logprint("Client request to close connection")
        # Return -1 to indicate closed connection
        return -1
    db.execute("SELECT uid, username, passwd, salt, lastlogin FROM user WHERE username=?", (ulogincred['username'], ))
    result = db.fetchone()
    if (result==None):
        # If the user does not exist
        error = "User \""+ulogincred['username']+"\" not found."
        logprint(error)
        result = mfp_encode("login", 0, error)
        conn.send(result)
        return 0
    else:
        # If the user exists
        db_user['uid'] = result[0]
        db_user['username'] = str(result[1])
        db_user['password'] = str(result[2])
        db_user['salt'] = str(result[3])
        db_user['lastlogin'] = result[4]
        logprint("Userinfo in Database")
        logpprint(db_user)
        logprint("Submitted uPWD:\t" + ulogincred['password'])
        ulogincred['password'] = hashlib.md5(ulogincred['password']+db_user['salt']).hexdigest()
        logprint("Encrypted uPWD:\t" + ulogincred['password'])
        logprint("Database PWD:\t" + db_user['password'])
        # Check if password matches
        if (ulogincred['password'] ==  db_user['password']):
            user = {
                "uid"       :   db_user['uid'],
                "username"  :   db_user['username'],
                "lastlogin" :   db_user['lastlogin'],
            }
            # Update lastlogin
            logprint("Updating lastlogin")
            if (user['lastlogin'] == ""): user['lastlogin'] = time.time()
            db.execute("UPDATE user SET lastlogin=? WHERE uid=?", (time.time(), user['uid'], ))
            dbconn.commit()

            logprint(user['username'] + " logged in.")
            result = mfp_encode("login", 1, user)
            conn.send(result)
            # Kick all previous logged in client offline
            toBeKicked = []
            for item in activeClients:
                if (activeClients[item]["uid"] == user['uid']):
                    logprint("Previous died client found: " + str(item))
                    # Register client as logged out
                    activeClients[item]["uid"] = 0
                    activeClients[item]["username"] = ""
                    activeClients[item]["ALIVE"] = 0
                    item.close()
                    logprint("Previous died connection closed")
                    toBeKicked.append(item)
            for i in toBeKicked:
                logprint("Remove "+ str(i) +" from activeClients list.")
                del activeClients[i]
            # Register client as logged in
            activeClients[conn]["uid"] = user['uid']
            activeClients[conn]["username"] = user['username']

            # Wait for client to initialize listener
            time.sleep(1)

            # Check for unapproved friend requests
            logprint("Checking for friend requests")
            db.execute("SELECT friendrequests FROM user WHERE uid=?", (user["uid"],))
            fr = mfp_encode("", 1, "You have " + str(len(json.loads(db.fetchone()[0]))) + " new friend requests")
            conn.sendall(fr)
            time.sleep(2)
            
            # Check for unread message
            logprint("Checking for unread messages")
            db.execute("SELECT * FROM messages WHERE targetuid=? AND unread=1", (user["uid"],))
            unread = db.fetchall()
            if (unread != None):
                for i in unread:
                    unreadmsg = {
                        "msgid" :   i[0],
                        "fromuid"    :   i[1],
                        "targetuid"  :   i[2],
                        "sendtime" :   i[3],
                        "message"   :   str(i[4]),
                        "unread"    :   i[5],
                    }
                    logprint("Unread message:")
                    logpprint(unreadmsg)
                    db.execute("SELECT username FROM user WHERE uid=?", (unreadmsg["fromuid"],))
                    fromUsername = db.fetchone()
                    msg = {
                        "username"  :   str(fromUsername[0]),
                        "sendtime"  :   unreadmsg["sendtime"],
                        "body"      :   unreadmsg["message"],
                    }
                    msg = mfp_encode("msg", 1, msg)
                    conn.sendall(msg)
                    db.execute("UPDATE messages SET unread=0 WHERE msgid=?", (unreadmsg["msgid"], ))
                    dbconn.commit()
                    time.sleep(0.2)
            else:
                logprint("no unread messages")
            return user
        else:
            error = "Incorrect password"
            logprint(error)
            result = mfp_encode("login", 0, error)
            conn.send(result)
            return 0


def addfriend(conn, dbconn, user, data):
    db = dbconn.cursor()
    logprint("User " + str(user['username']) + " request to add " + data['username'] + " as a friend")
    logprint("Fetching user info")
    db.execute("SELECT uid, username, friends, friendrequests FROM user WHERE username=?", (data["username"],))
    result = db.fetchone()
    # Check if the user exists
    if (result==None):
        # Not exists
        error = "User \"" + data["username"] + "\" not found."
        logprint(error)
        error = mfp_encode("msg", 0, error)
        conn.sendall(result)
    else:
        logprint("User found. Processing friends info")
        # Exists
        target = {
            "uid"       :   result[0],
            "username"  :   str(result[1]),
            "friends"   :   json.loads(str(result[2])),
            "friendrequests" :   json.loads(str(result[3])),
        }
        # Prevent add self
        if (target['uid'] == user['uid']):
            logprint(user['username'] + " tried to add self as a friend")
            error = "You cannot add yourself as a friend."
            error = mfp_encode("addf", 0, error)
            conn.sendall(error)
            return
        if (user['uid'] not in target['friends']):
            if (user['uid'] not in target['friendrequests']):
                target['friendrequests'].append(user['uid'])
            else:
                logprint(user['username'] + " is already in " + target['username'] + " 's friendrequest list")
                error = "You have already requested to add " + target['username'] + " as a friend."
                error = mfp_encode("addf", 0, error)
                conn.sendall(error)
                return
        else:
            logprint(user['username'] + " is already a friend with " + target['username'])
            error = "You are already friends with " + target['username']
            error = mfp_encode("addf", 0, error)
            conn.sendall(error)
            return
        target['friendrequests'] = json.dumps(target['friendrequests'])
        db.execute("UPDATE user SET friendrequests=? WHERE uid=?", (target['friendrequests'], target['uid'],))
        # dbconn.commit() # Not neccessary because in messenger it will commit
        time.sleep(0.2)
        msgdata = {
            "username"  :   target['username'],
            "body"      :   user['username']+" has sent you a friend request"
        }
        messenger(conn, dbconn, SYSTEM, msgdata)
        logprint(user['username'] + " added to " + target['username'] + "'s friendrequests list")
        feedback = "Friend request sent to " + target['username'] + "."
        feedback = mfp_encode("addf", 1, feedback)
        conn.sendall(feedback)
        return


def changepwd(conn, dbconn, user, data):
    db = dbconn.cursor()
    logprint("User " + str(user['username']) + " request to change password")
    logprint("Fetching user info")
    rs = db.execute("SELECT username, passwd, salt FROM user WHERE uid=?", str(user['uid'],))
    rs = rs.fetchone()
    db_user = {
        'username': str(rs[0]),
        'password': str(rs[1]),
        'salt': str(rs[2])
    }
    logpprint(data)
    if (db_user['password'] == hashlib.md5(data['oldpwd']+db_user['salt']).hexdigest()):
        logprint(db_user['username'] + " old password verified")
        if (data['newpwd1'] == data['newpwd2']):
            logprint("Changing password for " + db_user['username'])
            newpwd = hashlib.md5(data['newpwd1']+db_user['salt']).hexdigest()
            logprint("NEWPWD = " + newpwd)
            db.execute("UPDATE user SET passwd=? WHERE uid=?", (str(newpwd), str(user['uid']), ))
            dbconn.commit()
            data = db_user['username'] + " password changed"
            logprint(data)
            data = mfp_encode("chpwd", 1, data)
            conn.sendall(data)
        else:
            error = db_user['username'] + " newpwd1 newpwd2 mismatch"
            logprint(error)
            error = mfp_encode("chpwd", 0, error)
            conn.sendall(error)
    else:
        error = db_user['username'] + " old password incorrect."
        logprint(error)
        error = mfp_encode("chpwd", 0, error)
        conn.sendall(error)


def comments(conn, dbconn, user, data):
    db = dbconn.cursor()
    logprint(user['username'] + " comments post " + str(data['pid']))
    logprint("Fetching postid=" + str(data))
    db.execute("SELECT postid, fromuid, sendtime, body, comments, likes, readby FROM posts WHERE postid=?", (data['pid'], ))
    post = db.fetchone()
    post = {
        "postid"    :   post[0],
        "fromuid"   :   post[1],
        "sendtime"  :   post[2],
        "body"      :   post[3],
        "comments"  :   post[4],
        "likes"     :   post[5],
        "readby"    :   post[6]
    }
    logpprint(post)
    post['comments'] = json.loads(post['comments'])
    post['comments'].append([user['username'], data['body']])
    post['comments'] = json.dumps(post['comments'])
    db.execute("UPDATE posts SET comments=? WHERE postid=?", (post['comments'], data['pid']))
    db.execute("SELECT username FROM user WHERE uid=?", (post['fromuid'], ))
    statususername = db.fetchone()[0]
    msgdata = {
        "username"  :   statususername,
        "body"      :   user['username']+" has commented on your status"
    }
    messenger(conn, dbconn, SYSTEM, msgdata)
    # dbconn.commit()   # The messenger will commit


def feeds(conn, dbconn, user, data):
    db = dbconn.cursor()
    db.execute("SELECT friends FROM user WHERE uid=?", (user["uid"],))
    friendlist = db.fetchone()[0]
    friendlist = json.loads(friendlist)
    logprint("Friends: ")
    logprint(friendlist)
    unreadlist = []
    for friend in friendlist:
        logprint("Fetching username of uid=" + str(friend))
        db.execute("SELECT username FROM user WHERE uid=?", (friend, ))
        friendname = db.fetchone()[0]
        logprint(friendname)
        logprint("Fetching " + friendname + " 's posts")
        db.execute("SELECT postid, fromuid, sendtime, body, comments, likes, readby FROM posts WHERE fromuid=? ORDER BY sendtime ASC", (friend, ))
        allposts = db.fetchall()
        for singlepost in allposts:
            post = {
                "postid"    :   singlepost[0],
                "fromuid"   :   singlepost[1],
                "username"  :   friendname,
                "sendtime"  :   singlepost[2],
                "body"      :   singlepost[3],
                "comments"  :   singlepost[4],
                "likes"     :   singlepost[5],
                "readby"    :   singlepost[6]
            }
            post['readby'] = json.loads(post['readby'])
            logpprint(post)
            if user['uid'] not in post['readby']:
                logprint("Fetching liked username")
                likeusernames = []
                post['likes'] = json.loads(post['likes'])
                for likeuid in post['likes']:
                    print(likeuid)
                    db.execute("SELECT username FROM user WHERE uid=?", (likeuid,))
                    likeusernames.append(db.fetchone()[0])
                post['likes'] = likeusernames
                logprint("Adding user to readby list")
                post['readby'].append(user['uid'])
                readby = json.dumps(post['readby'])
                logprint("Updating post readby")
                db.execute("UPDATE posts SET readby=? WHERE postid=?", (readby, post['postid']))
                dbconn.commit()
                unreadlist.append(post)
            else:
                logprint("Ignore, post already read")
    if (len(unreadlist) == 0):
        msg = mfp_encode("feeds", 0, "No new feeds")
    else:
        msg = mfp_encode("feeds", 1, unreadlist)
    conn.sendall(msg)
    return


def likes(conn, dbconn, user, data):
    db = dbconn.cursor()
    logprint(user['username'] + " likes post " + str(data))
    logprint("Fetching postid=" + str(data))
    db.execute("SELECT postid, fromuid, sendtime, body, comments, likes, readby FROM posts WHERE postid=?", (data, ))
    post = db.fetchone()
    post = {
        "postid"    :   post[0],
        "fromuid"   :   post[1],
        "sendtime"  :   post[2],
        "body"      :   post[3],
        "comments"  :   post[4],
        "likes"     :   post[5],
        "readby"    :   post[6]
    }
    post['likes'] = json.loads(post['likes'])
    logpprint(post)
    if user['uid'] not in post['likes']:
        post['likes'].append(user['uid'])
        post['likes'] = json.dumps(post['likes'])
        db.execute("UPDATE posts SET likes=? WHERE postid=?", (post['likes'], data))
        db.execute("SELECT username FROM user WHERE uid=?", (post['fromuid'], ))
        statususername = db.fetchone()[0]
        msgdata = {
                "username"  :   statususername,
                "body"      :   user['username']+" liked your status"
            }
        messenger(conn, dbconn, SYSTEM, msgdata)
        # dbconn.commit()   # The messenger will commit


def messenger(conn, dbconn, user, data):
    db = dbconn.cursor()
    sendtime = int(time.time())
    data["username"] = str(data["username"])
    logprint("User " + str(user) + " sends a message to " + data["username"])
    db.execute("SELECT uid, username, friends FROM user WHERE username=?", (data["username"],))
    result = db.fetchone()
    # Check if the user exists
    if (result==None):
        # Not exists
        error = "User \"" + data["username"] + "\" not found."
        logprint(error)
        error = mfp_encode("msg", 0, error)
        conn.sendall(error)
    else:
        # Exists
        target = {
            "uid"       :   result[0],
            "username"  :   str(result[1]),
            "friends"   :   str(result[2]),
        }
        db.execute("INSERT INTO messages (fromuid, targetuid, sendtime, body) VALUES (?,?,?,?)", (user["uid"], target["uid"], sendtime, data["body"]))
        msgid = db.lastrowid
        dbconn.commit()
        time.sleep(0.2) # Avoid disk I/O error due to rapid write database file can be slow
        # |------ Uncomment to enable message sent feedback ------|
        # result = json.dumps("msg", 1, "Message Sent")
        # conn.sendall(result)
        # |-------------------------------------------------------|
        # Check if user is online
        for item in activeClients:
            if (activeClients[item]["username"] == data["username"]):
                logprint(data["username"] + " is currently online. Make message packet")
                msg = {
                    "username"  :   user['username'],
                    "sendtime"  :   sendtime,
                    "body"  :   data['body']
                }
                msg = mfp_encode("msg", 1, msg)
                logprint("Sending message to online client...")
                item.sendall(msg)
                logprint("Mark msgid=" + str(msgid) + " as read")
                db.execute("UPDATE messages SET unread=0 WHERE msgid=?", (msgid,))
                dbconn.commit()


def newstatus(conn, dbconn, user, data):
    db = dbconn.cursor()
    sendtime = int(time.time())
    logprint(user['username'] + " has requested to post a new status")
    db.execute("INSERT INTO posts (fromuid, sendtime, body) VALUES (?,?,?)", (user["uid"], sendtime, data))
    dbconn.commit()

def procfr(conn, dbconn, user, data):
    db = dbconn.cursor()
    logprint(user['username'] + " has requested to process its friendrequests")
    logprint("Fetching friendrequests")
    while True:
        db.execute("SELECT friends, friendrequests FROM user WHERE uid=?", (user["uid"],))
        result = db.fetchone()
        friends = json.loads(result[0])
        friendrequests = json.loads(result[1])
        nomore = True
        for i in friendrequests:
            nomore = False
            db.execute("SELECT username FROM user WHERE uid=?", (i,))
            uname = db.fetchone()[0]
            logprint("Friendrequest: " + uname)
            fr = mfp_encode("procfr", 1, uname)
            conn.sendall(fr)
            agree = conn.recv(1024)
            agree = mfp_decode(agree)
            if (agree['data']['agree'] == "Y"):
                logprint("Agreed")
                if (i not in friends):
                    friends.append(i)
                    db.execute("SELECT friends FROM user WHERE uid=?", (i,))
                    targetfriends = json.loads(db.fetchone()[0])
                    if (user['uid'] not in targetfriends):
                        targetfriends.append(user['uid'])
                    targetfriends = json.dumps(targetfriends)
                    db.execute("UPDATE user SET friends=? WHERE uid=?", (targetfriends, i,))
                    # dbconn.commit()
                    # time.sleep(0.2)
                    
            friendrequests.remove(i)
            friends = json.dumps(friends)
            friendrequests = json.dumps(friendrequests)
            db.execute("UPDATE user SET friends=?, friendrequests=? WHERE uid=?", (friends, friendrequests, user['uid'],))
            dbconn.commit()
            time.sleep(0.2)
            msgdata = {
                "username"  :   uname,
                "body"      :   user['username'] + " has accepted your friend request"
            }
            print(msgdata)
            messenger(conn, dbconn, SYSTEM, msgdata)
            break # only process the first one
        if (nomore):
            uname = mfp_encode("procfr", 0, "")
            conn.sendall(uname)
            return


def viewfriend(conn, dbconn, user, data):
    db = dbconn.cursor()
    logprint(user['username'] + " has requested to view its friendlist")
    logprint("Fetching friends")
    db.execute("SELECT friends FROM user WHERE uid=?", (user["uid"],))
    friends = db.fetchone()[0]
    friends = json.loads(friends)
    friendlist = []
    for i in friends:
        db.execute("SELECT username FROM user WHERE uid=?", (i,))
        friendlist.append(db.fetchone()[0])
    friendlist = mfp_encode("viewf", 1, friendlist)
    conn.sendall(friendlist)


def wall(conn, dbconn, user, data):
    db = dbconn.cursor()
    walllist = []
    db.execute("SELECT uid, username, friends FROM user WHERE username=?", (data, ))
    walluser = db.fetchone()
    walluser = {
        "uid"       :   walluser[0],
        "username"  :   walluser[1],
        "friends"   :   walluser[2],
    }
    walluser['friends'] = json.loads(walluser['friends'])
    logpprint(walluser)
    if user['uid'] not in walluser['friends']:
        if (user['uid'] != walluser['uid']):
            msg = mfp_encode("feeds", 0, "You are not a friend with "+walluser['username'])
            conn.sendall(msg)
            return
    logprint("Fetching " + walluser['username'] + " 's posts")
    db.execute("SELECT postid, fromuid, sendtime, body, comments, likes, readby FROM posts WHERE fromuid=? ORDER BY sendtime ASC", (walluser['uid'], ))
    allposts = db.fetchall()
    for singlepost in allposts:
        post = {
            "postid"    :   singlepost[0],
            "fromuid"   :   singlepost[1],
            "username"  :   walluser['username'],
            "sendtime"  :   singlepost[2],
            "body"      :   singlepost[3],
            "comments"  :   singlepost[4],
            "likes"     :   singlepost[5],
            "readby"    :   singlepost[6]
        }
        post['readby'] = json.loads(post['readby'])
        logpprint(post)
        logprint("Fetching liked username")
        likeusernames = []
        post['likes'] = json.loads(post['likes'])
        for likeuid in post['likes']:
            print(likeuid)
            db.execute("SELECT username FROM user WHERE uid=?", (likeuid,))
            likeusernames.append(db.fetchone()[0])
            post['likes'] = likeusernames
        if user['uid'] not in post['readby']:
            logprint("Adding user to readby list")
            post['readby'].append(user['uid'])
            readby = json.dumps(post['readby'])
            logprint("Updating post readby")
            db.execute("UPDATE posts SET readby=? WHERE postid=?", (readby, post['postid']))
        walllist.append(post)
    dbconn.commit()

    if (len(walllist) == 0):
        msg = mfp_encode("feeds", 0, "No new feeds")
    else:
        msg = mfp_encode("feeds", 1, walllist)
    conn.sendall(msg)
    return





"""
 .oooooo..o                              o8o                        
d8P'    `Y8                              `"'                        
Y88bo.       .ooooo.   .oooo.o  .oooo.o oooo   .ooooo.  ooo. .oo.   
 `"Y8888o.  d88' `88b d88(  "8 d88(  "8 `888  d88' `88b `888P"Y88b  
     `"Y88b 888ooo888 `"Y88b.  `"Y88b.   888  888   888  888   888  
oo     .d8P 888    .o o.  )88b o.  )88b  888  888   888  888   888  
8""88888P'  `Y8bod8P' 8""888P' 8""888P' o888o `Y8bod8P' o888o o888o 
"""

# User Session
def clientthread(conn):
    global LOG
    # Connect to SQLite database
    dbconn = sqlite3.connect('database.db')
    db = dbconn.cursor()

    user = 0
    while (activeClients[conn]["ALIVE"] ==1):
        logprint("Current Active Clients: ")
        logpprint(activeClients)
        exit = False
        while (user == 0):
            user = login(conn, dbconn)
            # Close connection handler
            if (user == -1):
                logprint("Close connection.")
                conn.close()
                logprint("Remove conn from activeClients list.")
                del activeClients[conn]
                exit = True
                break
        if (exit):
            break

        data = ""
        while (data == ""):
            try:
                data = conn.recv(1024)
            except:
                print("Thread ERROR: Connection failed.")
                return


        data = mfp_decode(data)

        if (data['request'] == "addf"):
            addfriend(conn, dbconn, user, data['data'])

        # CHANGEPWD
        elif (data['request'] == "chpwd"):
            changepwd(conn, dbconn, user, data['data'])

        # COMMENTS
        elif (data['request'] == "comments"):
            comments(conn, dbconn, user, data['data'])

        # FEEDS
        elif (data['request'] == "feeds"):
            feeds(conn, dbconn, user, data['data'])

        # LIKES
        elif (data['request'] == "likes"):
            likes(conn, dbconn, user, data['data'])

        # LOGOUT
        elif (data['request'] == "logout"):
            data = "User " + str(user['username']) + " logged out"
            logprint(data)
            data = mfp_encode("logout", 1, data)
            conn.sendall(data)
            user = 0
            # Register client as logged out
            activeClients[conn]["uid"] = 0
            activeClients[conn]["username"] = ""

        # MENU
        elif (data['request'] == "menu"):
            logprint("User " + str(user['username']) + " requests menu")
            data = mfp_encode("menu", 1, MENU)
            conn.sendall(data)

        # MSG
        elif (data['request'] == "msg"):
            messenger(conn, dbconn, user, data['data'])

        # NEW STATUS
        elif (data['request'] == "newstatus"):
            newstatus(conn, dbconn, user, data['data'])

        # PROCESS FRIEND REQUESTS
        elif (data['request'] == "procfr"):
            procfr(conn, dbconn, user, data['data'])

        # SVERBOSE
        elif (data['request'] == "sverbose"):
            LOG = not LOG
            print("SVerbose: " + str(LOG))
        
        # VIEW FRIEND LIST
        elif (data['request'] == "viewf"):
            viewfriend(conn, dbconn, user, data['data'])

        # WALL
        elif (data['request'] == "wall"):
            wall(conn, dbconn, user, data['data'])

        # _IDLE_
        else:
            msg = mfp_encode("respond", 0, data)
            conn.sendall(msg)

















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

# Setup server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
try:
    s.bind((HOST, PORT))
except socket.error , msg:
    print '\tERROR: Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
    sys.exit()
s.listen(10)
print("\n\nMini Facebook server started.")

# Start accept client connection
while 1:
    conn, addr = s.accept()
    if (LOG): print 'Connected with ' + addr[0] + ':' + str(addr[1])
    thread.start_new_thread(clientthread ,(conn,))
    activeClients[conn] = {
        "uid"   :   0,
        "username": "",
        "ALIVE" :   1
    }

s.close()


