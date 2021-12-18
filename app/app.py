import pprint

from flask import Flask, redirect, url_for, request, render_template
import requests
import json
import os
import re
from elasticsearch import Elasticsearch, NotFoundError
import configparser
import ldap
import socket
from typing import Any
from datetime import datetime

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
        s = re.sub(
            r'(?:\${(j|\${::-j})(n|\${::-n})(d|\${::-d})(i|\${::-i}):((l|\${::-l})(d|\${::-d})(a|\${::-a})(p|\${::-p})|))',
            '', m.group(0)).replace('://', '').replace('}', '')
        connect = {'ip': re.findall(r'[0-9]+(?:\.[0-9]+){3}', s),
                   'port': re.findall(r'(?::[0-9]{1,5}\/)', s),
                   'path': re.findall(r'(?:\/.{1,})', s)
                   }

        try:
            con = ldap.initialize("ldap://" + connect['ip'][0] + connect['port'][0].replace('/', ''), bytes_mode=False)
        except:
            return 0
        else:
            con.protocol_version = ldap.VERSION3
            con.set_option(ldap.OPT_REFERRALS, 0)
            con.set_option(ldap.OPT_NETWORK_TIMEOUT, 5.0)
            try:
                con.simple_bind_s()
            except:
                return 0
            else:
                search_scope = ldap.SCOPE_SUBTREE
                try:
                    msgid = con.search(connect['path'][0].strip("/"), search_scope)
                except:
                    return 0
                else:
                    result_status, result_data = con.result(msgid, 0)
                    if result_data[0][1]['javaCodeBase']:
                        r = requests.get(result_data[0][1]['javaCodeBase'][0].decode('ascii').strip('/') + '/' +
                                         result_data[0][1]['javaFactory'][0].decode('ascii') + '.class',
                                         stream=True
                                         )
                        if r.status_code == 200:
                            with open(
                                    'payloads/' + str(connect['ip'][0]) + '_' + result_data[0][1]['javaFactory'][0].decode(
                                        'ascii') + '.class', 'wb') as f:
                                for chunk in r:
                                    f.write(chunk)
                                f.close()


def check_geoip_mapping(es, index):
    if es.indices.exists(index=index):
        es.indices.put_mapping(
            index=index,
            body={
                "properties": {
                    "geo": {"properties": {"location": {"type": "geo_point"}}}
                }
            },
        )


def check_geoip_pipeline(es, pipeline):
    try:
        # check if the geoip pipeline exists. An error
        # is raised if the pipeline does not exist
        es.ingest.get_pipeline(id=pipeline)
    except NotFoundError:
        # geoip pipeline
        body = {
            "description": "Add geoip info",
            "processors": [
                {
                    "geoip": {
                        "field": "src_ip",  # input field of the pipeline (source address)
                        "target_field": "geo",  # output field of the pipeline (geo data)
                        "database_file": "GeoLite2-City.mmdb",
                    }
                }
            ],
        }
        es.ingest.put_pipeline(id=pipeline, body=body)


def check_index(es, index):
    if not es.indices.exists(index=index):
        #  create index
        es.indices.create(index=index)


def reportHit(request):
    config = read_conf()
    if config['ELASTICSEARCH']['enabled'] == "true":
        options: dict[str, Any] = {}
        options["http_auth"] = (config['ELASTICSEARCH']['username'], config['ELASTICSEARCH']['password'])
        options["scheme"] = "https"
        options["use_ssl"] = True
        options["ssl_show_warn"] = False
        options["verify_certs"] = False
        es = Elasticsearch(f"{config['ELASTICSEARCH']['host']}:{config['ELASTICSEARCH']['port']}", **options)
        check_index(es, config['ELASTICSEARCH']['index'])
        check_geoip_mapping(es, config['ELASTICSEARCH']['index'])
        check_geoip_pipeline(es, config['ELASTICSEARCH']['pipeline'])
        report = {}
        for header in request.headers:
            report[header[0]] = str(header[1])
        if request.form.items():
            for fieldname, value in request.form.items():
                report[fieldname] = report[value]
        report['src_ip'] = request.remote_addr
        report['timestamp'] = datetime.now().isoformat()
        report['sensor'] = config['DEFAULT']['name']

        es.index(
            index=config['ELASTICSEARCH']['index'], doc_type='_doc', document=report, pipeline=config['ELASTICSEARCH']['pipeline']
        )
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
    if config['DEFAULT']['debug'] == 'false':
        app.run(debug=False, host=config['DEFAULT']['ip'], port=int(config['DEFAULT']['port']))
    else:
        app.run(debug=True, host=config['DEFAULT']['ip'], port=int(config['DEFAULT']['port']))
