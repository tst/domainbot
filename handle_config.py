import os
import sys
import logging
import ConfigParser

config = ConfigParser.SafeConfigParser()
config.read("config.ini")

## get variables
USERNAME = config.get("reddit", "username")
PASSWORD = config.get("reddit", "password")

PATHTODB = config.get("technical", "pathtodb")
USER_AGENT = config.get("technical", "user_agent")

MESSAGE_SUBJECT = config.get("message", "subject", raw = True)
MESSAGE_MESSAGE = config.get("message", "message", raw = True).replace("\n", "\n\n")

MESSAGE_PRIVATE_SUBJECT = config.get("message", "privatesubject", raw = True)
MESSAGE_PRIVATE_MESSAGE = config.get("message", "privatemessage", raw = True).replace("\n", "\n\n")

ALLOWED_DOMAINS = config.get("behavior", "allowed_domains").split(",")
SUBMISSION_LIMIT = int(config.get("behavior", "submission_limit"))
THRESHOLD_PERCENTAGE = int(config.get("behavior", "threshold_percentage"))
THRESHOLD_TOTAL = int(config.get("behavior", "threshold_total"))

if config.get("technical", "debug") == "on":
    logging.basicConfig(level=logging.DEBUG) 
else:
    logging.basicConfig(level=logging.ERROR) 


# if USERNAME and PASSWORD isn't set the bot will use the environment variables
if USERNAME in ["username", ""]:
    try:
        USERNAME = os.environ['DOMAINBOT_USERNAME']
    except KeyError:
        sys.exit("Please add the username or set the environment variable DOMAINBOT_USERNAME")

if PASSWORD in ["password", ""]:
    try:
        PASSWORD = os.environ['DOMAINBOT_PASSWORD']
    except KeyError:
        sys.exit("Please add the password or set the environment variable STORYBOT_PASSWORD")


# check for sane values in THRESHOLD
if THRESHOLD_PERCENTAGE == 0:
    sys.exit("THRESHOLD_PERCENTAGE = 0: Do you REALLY want to report every user? Think about it for a minute.")
if THRESHOLD_TOTAL < 4:
    sys.exit("THRESHOLD_TOTAL < 4: Do you REALLY want to report users with less than 4 submissions? \
             C'mon up it a bit")
