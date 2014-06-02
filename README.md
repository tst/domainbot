# DomainBot for Reddit

## Description
DomainBot checks if users post predomately links from a few domains. You can filter out domains which should be allowed, set the limit per domain and total limit of minimum submissions required. Self posts are ignored. If the limit is exceeded the bot will send a modmail to the subreddit. Subreddits can be added by going the bot a mod privilege or by hand using SQL (advanced).


## Installation

The bot runs on Python 2.7 with the following package:

* [PRAW aka. Python Reddit API Wrapper](https://github.com/praw-dev/praw)

which can be easily installed using pip

    pip install praw


## Configuration

Open the config.ini and edit it accordingly. These are the things you have to edit:

    [reddit]
    username=username
    password=password

    [behavior]
    ; these domains won't trigger a modmail
    allowed_domains=i.imgur.com,imgur.com,youtube.com,youtu.be,*.deviantart.com
    ; how many submissions should be crawled?
    submission_limit=20
    ; how many submissions per domain in % are allowed?
    threshold_percentage=20
    ; how many submissions should the users have at least?
    threshold_total=8
    ; skips test if the submission is in allowed_domains
    skipped_allowed_domains=on

    [technical]
    ; debug = on / off
    ; set debug = off to run the bot in production (i.e. sending messages)
    debug=on 


## Usage

### General

*I would recommend that you bot's account should have some link karma so that it can send messages without captcha restrictions.*

If you execute the bot.py with

    python bot.py

it will crawl the /new page and check each new submissions. For each submission it will crawl the poster's submission history and determine the amount of submissions which are from one domain. If the poster exceeds the limits the bot will send a modmail to the examined subreddit.

### Generate domain stats for specific user

You can send a message to the bot with the subject "scan" and the text "/u/USERNAME". USERNAME is the name of user you want domain statistics about. 

## Requests / Questions

If you have any requests or actions feel free to open an issue, message me on reddit ([/u/tst__](http://www.reddit.com/message/compose/?to=tst__)) or write me an email.

