import praw
import time
import sqlite3
import os
import sys
import logging
import math
import ConfigParser
from handle_config import *


def is_allowed(domain, ALLOWED_DOMAINS):
    if domain in ALLOWED_DOMAINS:
        return True
    for d in ALLOWED_DOMAINS:
        # if wildcard notation is used
        if "*." in d:
            if d[2:] in domain:
                return True
    return False


def crawl_author(author_name, r, c, conn):
    # get Redditor instance
    author = r.get_redditor(author_name)

    # check if user exists and get it's last crawled submission
    c.execute("SELECT submission_id FROM users WHERE username = ? ORDER BY time_utc DESC LIMIT 1", (author_name, ))
    ph = c.fetchone()
    author_placeholder = ph[0] if ph is not None else None

    # crawl user's submissions

    logging.debug(SUBMISSION_LIMIT)
    logging.debug(author_placeholder)
    author_submissions = author.get_submitted(sort="new", time="all", limit=SUBMISSION_LIMIT, \
                                              place_holder=author_placeholder)

    # add new submissions
    for submission in author_submissions:
        # skip if self
        if submission.is_self:
            continue
        values = (submission.author.name, submission.domain, submission.id, submission.created_utc)
        c.execute("INSERT OR IGNORE INTO users (username, domain, submission_id, time_utc) \
                   VALUES (?, ?, ?, ?)", values)
    conn.commit()
    return


def create_author_stats(author_name, c): 
    # check for domain distribution
    c.execute("""SELECT domain, (COUNT(*) * 100 / (SELECT COUNT(*) FROM users WHERE username = ? )) 
              AS perc FROM users WHERE username = ? GROUP BY domain HAVING (SELECT COUNT(*) FROM
              users WHERE username = ?) > ? ORDER BY perc DESC;""", (author_name, author_name,
                                                                     author_name, THRESHOLD_TOTAL))
    
    frequent_domains = c.fetchall()
    
    logging.debug(frequent_domains)
    
    send_modmail = False
    # Check allowed domains (ALLOWED_DOMAINS)
    
    for (domain, percentage) in frequent_domains:
        if (percentage > THRESHOLD_PERCENTAGE
            and "self." not in domain
            and not is_allowed(domain, ALLOWED_DOMAINS)):
            send_modmail = True

    return (send_modmail, frequent_domains)
        

def send_author_stats(author_name, frequent_domains, subreddit = None, to_user = None):
    if subreddit:
        to = "/r/" +  subreddit
        subject = MESSAGE_SUBJECT % (author_name)
        message = MESSAGE_MESSAGE % (subreddit, author_name)
    else:
        to = to_user
        subject = MESSAGE_PRIVATE_SUBJECT % (author_name)
        message = MESSAGE_PRIVATE_MESSAGE % (to_user, author_name)
       
    max_domains = int(math.ceil(1.0 / (float(THRESHOLD_PERCENTAGE) / 100)))
    
    # post message if not frequent_domains is empty aka. not enough submissions

    if not frequent_domains:
        message += "\n\n* /u/%s doesn't have enough submissions" % (author_name)
    else:

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


# login to Reddit
r = praw.Reddit(user_agent=USER_AGENT)
r.login(USERNAME, PASSWORD)

# connect to DB
conn = sqlite3.connect(PATHTODB)
c = conn.cursor()

# create the tables if it don't exist
c.execute("CREATE TABLE IF NOT EXISTS checked_ids (id TEXT);");
c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT, domain TEXT, submission_id TEXT UNIQUE, time_utc TEXT);");
c.execute("CREATE TABLE IF NOT EXISTS watched_subreddits (subreddit TEXT UNIQUE);");


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
        
        # update user's submission
        crawl_author(x.author.name, r, c, conn)
      
        send_modmail, frequent_domains = create_author_stats(x.author.name, c)
        
        if send_modmail:
            # Send modmail 
            send_author_stats(author_name = x.author.name, frequent_domains = frequent_domains, \
                              subreddit = subreddit)


        # Insert id into the database to that it won't be rechecked
        c.execute("INSERT INTO checked_ids VALUES (?)", (x.id, ))
        conn.commit()

# read messages
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
    
    # request to scan
    if "scan" in new_message.subject:
        try:
            # skip if format not correct
            if "/u/" not in new_message.body:
                continue
            
            author = new_message.body[3:]
            logging.debug("Requesting stats about /u/%s" % author)
            
            crawl_author(author, r, c, conn)
            _, frequent_domains = create_author_stats(author, c)
            send_author_stats(author_name = author, frequent_domains = frequent_domains, \
                              to_user = new_message.author.name)
        except Exception as e:
            logging.error(e)

    new_message.mark_as_read()

conn.close()
