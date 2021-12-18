# log4j-honeypot-flask
Internal network honeypot for detecting if an attacker or insider threat scans your network for log4j CVE-2021-44228

This can be installed on a workstation or server, either by running the Python app/app.py script directly (you'll need python3, Flask, and Requests) or as a Docker container.

You will need to set some environment variables (or hard-code them into the script):
WEBHOOK_URL=your Teams, Slack or Mattermost webhook URL to receive notifications
HONEYPOT_NAME=unique name for this honeypot so you know where the alerts came from
HONEYPOT_PORT=8080 or whatever port you want it to listen on

Important Note: This is a LOW-INTERACTION honeypot meant for internal active defense. It is not supposed to be vulnerable or let attackers get into anything.

All it does is watch for suspicious string patterns in the requests (form fields and HTTP headers) and alert you if anything weird comes through by sending a message 
on Teams or Slack.

# Example running via Docker:

```
docker build -t log4j-honeypot-flask:latest .

docker run -d -p 8080:8080 -e WEBHOOK_URL=https://yourwebhookurl -e HONEYPOT_NAME=dmz_log4j_hp log4j-honeypot-flask
```

# Example running via command line:

```
export WEBHOOK_URL=https://yourwebhookurl

export HONEYPOT_NAME=LittleBobbyJNDI

export HONEYPOT_PORT=8081

python3 app/app.py
```
