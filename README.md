# DomainBot for Reddit

## Description
DomainBot checks if users post predomately links to one domain. 


## Installation

The bot runs on Python 2.7 with the following package:

* [PRAW aka. Python Reddit API Wrapper](https://github.com/praw-dev/praw)

which can be easily installed using pip

    pip install praw


## Configuration

Open the config.ini and edit it accordingly. These are the things you have to edit:

    [reddit]
    username=username ; reddit username of your bot
    password=password ; reddit password of your bot
    subreddits=pics,politics ; subreddit in which the bot should work separated by comma

    [technical]
    pathtodb=/home/tim/domainbot/db.db ; path to your bot's database, just use your bot's directory + db.db

## Usage

*I would recommend that you bot's account should have some link karma so that it can send messages without captcha restrictions.*

If you execute the bot.py with

    python bot.py

it will crawl the /new page and check each new submissions. For each submission it will crawl the poster's submission history and determine the amount of submissions which are from one domain.

## Requests / Questions

If you have any requests or actions feel free to open an issue, message me on reddit ([/u/tst__](http://www.reddit.com/message/compose/?to=tst__)) or write me an email.

