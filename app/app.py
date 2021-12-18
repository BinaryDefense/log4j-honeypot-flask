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
    pprint.pprint(request)
    regex = re.compile(
        r'/(?:\${(j|\${::-j})(n|\${::-n})(d|\${::-d})(i|\${::-i}):((l|\${::-l})(d|\${::-d})(a|\${::-a})(p|\${::-p})|).*})/gm'
    )
    m = re.match(regex, str(request))
    if m:
        pprint.pprint(m.group(0))


def reportHit(request):
    return 0


app = Flask(__name__, template_folder='templates')


@app.route("/", methods=['POST', 'GET', 'PUT', 'DELETE'])
def homepage():
    regex = re.compile(r'^\${*')
    for header in request.headers:
        print(header)
        if re.search(regex, str(header[1])):
            getPayload(header[1])
            reportHit(header)
    if request.method == 'POST':
        for fieldname, value in request.form.items():
            print(value)
            if re.search(regex, str(value)):
                payload = getPayload(value)
                reportHit(value)
        return (
            "<html><head><title>Login Failed</title></head><body><h1>Login Failed</h1><br/><a href='/'>Try again</a></body></html>")
    else:
        return render_template('index.html')


if __name__ == '__main__':
    config = read_conf()
    app.run(debug=True, host=config['DEFAULT']['ip'], port=int(config['DEFAULT']['port']))
