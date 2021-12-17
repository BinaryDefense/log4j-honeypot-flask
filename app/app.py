import pprint

from flask import Flask, redirect, url_for, request, render_template
import requests
import json
import os
import re
import elasticsearch
import configparser
import ldap
import socket


def read_conf():
    config = configparser.ConfigParser()
    if config.read('config.ini'):
        return config
    else:
        return 0


def getPayload(request):
    connect = ldap.initialize(request)
    connect.set_option(ldap.OPT_REFERRALS, 0)
    connect.simple_bind()
    result = connect.search_s('Basic/Command/Base64/dG91Y2ggL3RtcC9leHBsb2l0')
    pprint.pprint(result)

def reportHit(request):
    return 0


app = Flask(__name__, template_folder='templates')


@app.route("/", methods=['POST', 'GET', 'PUT', 'DELETE'])
def homepage():
    regex = re.compile(r'^\${*')
    for header in request.headers:
        print(header)
        if re.search(regex, str(header[1])):
            reportHit(request)
    if request.method == 'POST':
        for fieldname, value in request.form.items():
            print(value)
            if re.search(regex, str(value)):
                reportHit(request)
        return (
            "<html><head><title>Login Failed</title></head><body><h1>Login Failed</h1><br/><a href='/'>Try again</a></body></html>")
    else:
        return render_template('index.html')


if __name__ == '__main__':
    getPayload('192.168.8.120:1389')
    config = read_conf()
    app.run(debug=False, host=config['DEFAULT']['ip'], port=int(config['DEFAULT']['port']))
