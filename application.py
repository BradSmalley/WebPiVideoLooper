from flask import Flask
from flask import render_template
from configparser import ConfigParser

import socket

app = Flask("__name__")

ip = ""
hostname = ""


def __init__():

    global hostname
    hostname = socket.gethostname()
    global ip
    ip = socket.gethostbyname(hostname)
    print("Your Computer Name is:" + hostname)
    print("Your Computer IP Address is:" + ip)

    config = ConfigParser()
    config.read("WebPiVideoLooper.ini")


@app.route("/looper/")
def looper():
    global ip
    return render_template("index.html", addr=ip)



