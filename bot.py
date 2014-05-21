import praw
import time
import sqlite3
import os
import sys
import logging
import math
import ConfigParser

config = ConfigParser.SafeConfigParser()
config.read("config.ini")

## get variables
USERNAME = config.get("reddit", "username")
PASSWORD = config.get("reddit", "password")
PATHTODB = config.get("technical", "pathtodb")
USER_AGENT = config.get("technical", "user_agent")
SUBREDDITS = config.get("reddit", "subreddit")
MESSAGE_SUBJECT = config.get("message", "subject", raw = True)
MESSAGE_MESSAGE = config.get("message", "message", raw = True).replace("\n", "\n\n")
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


# login to Reddit
r = praw.Reddit(user_agent=USER_AGENT)
r.login(USERNAME, PASSWORD)

# connect to DB
conn = sqlite3.connect(PATHTODB)
c = conn.cursor()

# create the tables if it don't exist
c.execute("CREATE TABLE IF NOT EXISTS checked_ids (id TEXT);");
c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, domain TEXT, submission_id TEXT, time_utc TEXT);");
c.execute("CREATE TABLE IF NOT EXISTS watched_subreddits (subreddit TEXT);");


#for subreddit in SUBREDDITS.split(","):
c.execute("SELECT subreddit FROM watched_subreddits")
srs = c.fetchall()
for sr in srs:
    subreddit = sr[0]
    # get the newest submissions
    new_submissions = r.get_subreddit(subreddit).get_new()

    ## check every new submission
    for x in new_submissions:
        
        # Skip the submission if it's already checked
        c.execute("SELECT id FROM checked_ids WHERE id = ?", (x.id,))
        if c.fetchone() is not None:
            continue
        
        # Skip if the author's account is deleted
        if x.author is None:
            continue
        
        
        # check if user exists and get it's last crawled submission
        c.execute("SELECT submission_id FROM users WHERE username = ? ORDER BY time_utc DESC LIMIT 1", (x.author.name, ))
        ph = c.fetchone()
        author_placeholder = ph[0] if ph is not None else None


        # crawl user's submissions

        logging.debug(SUBMISSION_LIMIT)
        logging.debug(author_placeholder)
        author_submissions = x.author.get_submitted(sort="new", time="all", limit=SUBMISSION_LIMIT, \
                                                    place_holder=author_placeholder)
        
        # add new submissions
        for submission in author_submissions:
            values = (submission.author.name, submission.domain, submission.id, submission.created_utc)
            c.execute("INSERT OR IGNORE INTO users (username, domain, submission_id, time_utc) \
                       VALUES (?, ?, ?, ?)", values)
        conn.commit()

        
        # check for domain distribution

        c.execute("""SELECT domain, (COUNT(*) * 100 / (SELECT COUNT(*) FROM users WHERE username = ? )) 
                  AS perc FROM users WHERE username = ? GROUP BY domain HAVING (SELECT COUNT(*) FROM
                  users WHERE username = ?) > ? ORDER BY perc DESC;""", (x.author.name, x.author.name,
                                                                         x.author.name, THRESHOLD_TOTAL))
        
        frequent_domains = c.fetchall()
        
        logging.debug(frequent_domains)
        
        send_modmail = False
        # Check allowed domains (ALLOWED_DOMAINS)
        for (domain, percentage) in frequent_domains:
            if (percentage > THRESHOLD_PERCENTAGE
                and domain not in ALLOWED_DOMAINS
                and "self." not in domain):
                send_modmail = True
        

        if send_modmail:
            # Send modmail 
            to = "/r/" +  subreddit
            subject = MESSAGE_SUBJECT % (x.author.name)
            message = MESSAGE_MESSAGE % (subreddit, x.author.name)
            
            max_domains = int(math.ceil(1.0 / (float(THRESHOLD_PERCENTAGE) / 100)))
            
            logging.debug(max_domains)

            message += "\n\n| Domain | Frequency |"
            message += "\n|:-----|:-----|"
            for (domain, percentage) in frequent_domains[:max_domains]:
                message += "\n| %s | %s%%" % (domain, percentage) 

            try:
                if logging.getLogger().getEffectiveLevel() <= logging.DEBUG:
                    logging.debug(to)
                    logging.debug(subject)
                    logging.debug(message)
                else:
                    # send messages only comments if DEBUG isn't on
                    r.send_message(to, subject, message)
            except Exception as e:
                logging.error(e)

        # Insert id into the database to that it won't be rechecked
        c.execute("INSERT INTO checked_ids VALUES (?)", (x.id, ))
        conn.commit()

        time.sleep(5)


# accept sub if get moderator
for new_message in r.get_unread(unset_has_mail=True, update_user=True):
    # add subreddit to watched subreddits if the bot got a mod invite
    if "invitation to moderate" in new_message.subject:
        try:
            _, _, _, sub = new_message.subject.split()
            sub = sub.replace("/r/", "")
            logging.debug(sub)
            r.accept_moderator_invite(sub)
            c.execute("INSERT OR IGNORE INTO watched_subreddits VALUES (?)", (sub, ))
            conn.commit()
        except Exception as e:
            logging.error(e)

    new_message.mark_as_read()

conn.close()
