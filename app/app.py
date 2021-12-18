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
    regex = re.compile(
        r'(?:\${(j|\${::-j})(n|\${::-n})(d|\${::-d})(i|\${::-i}):((l|\${::-l})(d|\${::-d})(a|\${::-a})(p|\${::-p})|).*})'
    )
    m = re.match(regex, str(request))
    if m:
        connect = []
        connect['ip'] = re.findall(r'[0-9]+(?:\.[0-9]+){3}', m.group(0))
        connect['port'] = re.findall(r'(?:[0-9]{1,5})', m.group(0))
        connect['path'] = re.findall(r'(?:\/[.]{1,})', m.group(0))
        pprint.pprint(connect)



def reportHit(request):
    print('LOLZ!!')
    return 0


app = Flask(__name__, template_folder='templates')


@app.route("/", methods=['POST', 'GET', 'PUT', 'DELETE'])
def homepage():
    exploited = False
    regex = re.compile(r'^\${*')
    for var in request.args:
        if re.search(regex, str(request.args.get(var))):
            getPayload(request.args.get(var))
            exploited = True
    for header in request.headers:
        print(header)
        if re.search(regex, str(header[1])):
            getPayload(header[1])
            exploited = True
    if request.method == 'POST':
        for fieldname, value in request.form.items():
            print(value)
            if re.search(regex, str(value)):
                payload = getPayload(value)
                exploited = True
        if exploited:
            reportHit(request)
        return (
            "<html><head><title>Login Failed</title></head><body><h1>Login Failed</h1><br/><a href='/'>Try again</a></body></html>")
    else:
        if exploited:
            reportHit(request)
        return render_template('index.html')



if __name__ == '__main__':
    config = read_conf()
    app.run(debug=True, host=config['DEFAULT']['ip'], port=int(config['DEFAULT']['port']))
