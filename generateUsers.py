import hashlib
import pprint
import random
import socket
import sqlite3
import string
import sys
import thread
import time


# Connect to SQLite database
dbconn = sqlite3.connect('database.db')
db = dbconn.cursor()


# Create Users

def generateSalt():
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    chars=[]
    for i in range(5):
        chars.append(random.choice(ALPHABET))
    return "".join(chars)

# [ username, encryptedPWD, PWDsalt ]
for i in range(1,6):
    salt = generateSalt()
    db.execute("INSERT INTO user (uid, username, password, salt) VALUES (?,?,?,?)", (str(i), "user"+str(i), hashlib.md5(hashlib.md5("u"+str(i)+"pwd").hexdigest()+salt).hexdigest(), salt))

# username: user#
# password: u#pwd

dbconn.commit()

dbconn.close()
