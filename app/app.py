from flask import Flask, redirect, url_for, request
import requests
import json
import os

#### Set your Slack or Teams or Mattermost webhook here, or in environment variable WEBHOOK_URL ####
webhook_url = ""
# For help setting up the webhook, see:
# Slack: https://api.slack.com/messaging/webhooks
# Teams: https://docs.microsoft.com/en-us/microsoftteams/platform/webhooks-and-connectors/how-to/add-incoming-webhook
# Mattermost: https://docs.mattermost.com/developer/webhooks-incoming.html

#### Set the name of this honeypot instance here, or in environment variable HONEYPOT_NAME ####
# (use a descriptive name so you know when alerts come in where they were triggered)
honeypot_name = "My log4j honeypot"

#### Set the port you want this honeypot to listen on. Recommend 8080 or 80
#### you can also use environment variable HONEYPOT_PORT
honeypot_port = 8080

if "HONEYPOT_NAME" in os.environ and os.environ["HONEYPOT_NAME"].strip() != "":
    honeypot_name = os.environ["HONEYPOT_NAME"]

if "WEBHOOK_URL" in os.environ and os.environ["WEBHOOK_URL"].strip() != "":
    webhook_url = os.environ["WEBHOOK_URL"].strip()

if "HONEYPOT_PORT" in os.environ and os.environ["HONEYPOT_PORT"].strip() != "":
    try:
        honeypot_port = int(os.environ["HONEYPOT_PORT"].strip())
    except:
        print("Invalid port: " + os.environ["HONEYPOT_PORT"])
        print("Reverting to port 8080 default")
        honeypot_port = 8080

app = Flask(__name__)

def reportHit(request):
    msglines = []
    msglines.append("Alert from log4j honeypot " + honeypot_name)
    msglines.append("Suspicious request received from IP: "+ request.remote_addr)
    msglines.append("Review HTTP headers for payloads:")
    msglines.append("```")
    for header in request.headers:
        msglines.append(str(header))
    for fieldname, value in request.form.items():
        msglines.append(str((fieldname, value)))
    msglines.append("```")

    msg = {'text':'\n '.join(msglines)}
    response = requests.post(
        webhook_url, data=json.dumps(msg),
        headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        print('Request to webhook returned an error %s, the response is:\n%s' % (response.status_code, response.text))

login_form = """<html>
<head><title>Secure Area Login</title></head>
<body>
<h1>Log in to Secure Area</h1>
<form method='post' action='/'>
  <b>Username:</b> <input name='username' type='text'/><br/>
  <b>Password:</b> <input name='password' type='password'/><br/>
  <input type='submit' name='submit'/>
</form>
</body></html>"""

@app.route("/", methods=['POST','GET','PUT','DELETE'])
def homepage():
    for header in request.headers:
        print(header)
        if "${" in header:
            reportHit(request)
    if request.method == 'POST':
        for fieldname, value in request.form.items():
            print(value)
            if "${" in value:
                reportHit(request)
        return("<html><head><title>Login Failed</title></head><body><h1>Login Failed</h1><br/><a href='/'>Try again</a></body></html>")
    else:
        return(login_form)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=honeypot_port)
