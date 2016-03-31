"""
Email alerting system for users that have pending moves on old games
(>24 hours since last update).

Uses a task queue since the query/email process may take awhile; other
modules should call start() to kick off a job.
"""
import datetime
import logging

from google.appengine.api import mail
from google.appengine.ext import deferred

from models import Game


def start():
    logging.info("Firing email task")
    deferred.defer(__email_task)

def __email_task():
    logging.info("Email task started")
    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    stale_game_q = Game.query(Game.active == True, Game.updated < yesterday)
    stale_games = {}
    for game in stale_game_q.iter():
        player_key = game.active_player_key
        if not player_key in stale_games:
            stale_games[player_key] = []
        stale_games[player_key].append(game.key.id())
    __send_emails(stale_games)
    logging.info("Email task complete")

def __send_emails(stale_games_dict):
    """ 
    Moving this into its own function gives us the flexibility
    to change the implementation later, such as by spawning 
    additional worker threads if the task takes too long.
    """
    for i in stale_games_dict:
        __send_email(player_key, game_list)

def __send_email(player_key, game_list):
    app_id = app_identity.get_application_id()
    player = player_key.get()
    # Getting the full model here so we can add an opt-out flag later
    subject = "Pending Liar's Dice games"
    body = "You have the following pending games:\n\n{}".format(
        '\n'.join(game_list))
    mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
        player.email,
        subject,
        body)
    logging.info("Sent email to {}".format(player.email))
