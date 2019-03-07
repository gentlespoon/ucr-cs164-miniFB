# ucr-cs164
Some python code, written in 2016, for ucr-cs164 networking course

```

### 1. What is it?

* An instant messaging app in virtualized network for CS 164 Computer Networks.
* Developed in Python, with TCP connection.

### 2. What can it do?

    Mini Facebook is capable in:
        Phase 1 -----------------------------------------------
            Connect to server                               OK
            Ask for password                                OK
            Login                                           OK
            Username clear text                             OK
            Password hidden                                 OK
            Log in if credentials are authenticate          OK
            Username/password hardcoded on server           OK      (Not hardcoded, stored in database instead)
            Provide a menu                                  OK
            Change password                                 OK
            Logout                                          OK
        Phase 2 -----------------------------------------------
            Send message                                    OK
            Online                                          OK
            Offline                                         OK
            Unread message count                            OK      (Directly show unread messages)
            See unread offline messages                     OK
            Real-time messages                              OK
        Phase 3 -----------------------------------------------
            Send friend request                             OK
            See unread offline friend request               OK
            Respond to friend request one by one            OK
            Real-time friend request                        OK
            Accept friend request                           OK
            See friends' status updates                     OK
            Post status                                     OK
            See Timeline (Wall)                             OK
            See News Feeds (last 10 updates)                OK
        Extra -------------------------------------------------
            Comment                                         OK
            Like                                            OK
            Number of new comments and likes                OK
            C/L appear next to the associated status        OK
            ---------------------------------------------------

### 3. How does it communicate?
    Client sends data from the main thread, and receives data from the listener thread.
    Server creates a thread for each connected client, receives and send data from the client thread.
    All communications between server and client are in JSON via TCP connections.

        MiniFacebookProtocal {
            Client => Server {
                "request"   :   "addf"  "chpwd" "comment"   "exit"  "feeds"
                                "like"  "login" "logout"    "menu"  "msg"
                                "newstatus" "post"  "procfr"    "sverbose"  "viewf" "wall"
                "data"      :   function specified data format, in dict {
                    addf {
                        string              :   username
                    }
                    chpwd {
                        "oldpwd"            :   old password for authenticate
                        "newpwd1"           :   new password
                        "newpwd2"           :   new password verification
                    }
                    comment {
                        "pid"               :   post id to be commented
                        "data"              :   comment body
                    }
                    exit {
                    }
                    feeds {
                    }
                    like {
                        "postid"            :   post id to be liked
                    }
                    login {
                        "username"          :   username
                        "password"          :   md5(password)
                    }
                    menu {
                    }
                    msg {
                        "username"          :   username
                        "body"              :   message body
                    }
                    newstatus {
                        string              :   status body
                    }
                    procfr {
                    }
                    sverbose {
                    }
                    viewf {
                    }
                    wall {
                        string              :   whose wall to see?
                    }
                }
            }
            Client <= Server {
                "respond"   :   "addf"  "chpwd" "comment"   "feeds" "like"
                                "login" "menu"  "msg"   "newstatus" "post" 
                                "viewf" "wall"  "welcome"
                "success"   :   "1"     "0"
                "data"      :   function specified data format, in dict {
                    addf {
                        error string
                    }
                    chpwd {
                        error string
                    }
                    comment {
                        error string
                    }
                    feeds {
                        list of dict posts {
                            "postid",
                            "fromuid",
                            "username",
                            "sendtime",
                            "body",
                            "comments",
                            "likes",
                            "readby"
                        }
                    }
                    like {
                        error string
                    }
                    login[0] {
                        error string
                    }
                    login[1] {
                        "uid"               :   uid
                        "username"          :   username
                        "lastlogin"         :   unix timestamp
                    }
                    menu {
                        menu string
                    }
                    msg {
                        "username"          :   username
                        "sendtime"          :   sendtime
                        "body"              :   message body
                    }
                    newstatus {
                        error string
                    }
                    procfr {
                        username string
                    }
                    viewf {
                    }
                    welcome {
                        welcome string
                    }
                }
            }
        }



### 4. Database schema
    Mini Facebook uses SQLite as the server-side database.
    The database schema is shown below:

        CREATE TABLE `messages` (
            `msgid` INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            `fromuid`   INTEGER NOT NULL,
            `targetuid` INTEGER NOT NULL,
            `sendtime`  INTEGER NOT NULL,
            `body`  TEXT,
            `unread`    INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE `posts` (
            `postid`    INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
            `fromuid`   INTEGER NOT NULL,
            `sendtime`  INTEGER NOT NULL,
            `body`  TEXT,
            `comments`  TEXT DEFAULT '[]',
            `likes`     TEXT DEFAULT '[]',
            `readby`    TEXT DEFAULT '[]'
        );
        CREATE TABLE `user` (
            `uid`   INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            `username`  TEXT NOT NULL,
            `passwd`    TEXT NOT NULL,
            `salt`  TEXT NOT NULL,
            `friends`   TEXT,
            `lastlogin` INTEGER
        );



### 5. Password encryption
    The user password is stored encrypted in the database.
    The encryption is md5( md5( pass ) + salt )
    Client submits ==> md5( password )
    Server retrieve salt and ==> md5( md5( pass ) + salt )
    Server compare the encrypted password with database password.
    Even in case of database breach, the original user password will not be exposed.



### 6. Known problems
    May get error due to race condition / db lock error.
    This project was done before I took concurrent / parallel programming course. 
    As a drawback of SQLite database, the multithreading accessing can be unstable due to database lock.
    It is possible that database was inaccessible (locked) when a large amount of users logged in.
