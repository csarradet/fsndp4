"""
Email alerting system for users that have pending moves on old games
(>24 hours since last update).

Uses a task queue since the query/email process may take awhile; other
modules should call start() to kick off a job.
"""
import datetime
import logging

from google.appengine.api import mail, app_identity
from google.appengine.ext import deferred

from models import Game


def start():
    logging.info("Firing email task")
    deferred.defer(__email_task)

def __email_task():
    try:
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
    except Exception as e:
        # It can be dangerous to allow exceptions to bubble up to the job
        # scheduler in this case -- depending on what happens, it can get
        # stuck in a retry loop and start spamming our users.
        # Instead, log the problem and raise a "stop doing that!" exception.
        msg = "Unhandled exception during email task, aborting"
        logging.exception(msg)
        raise deferred.PermanentTaskFailure(msg)


def __send_emails(stale_games_dict):
    """ 
    Moving this into its own function gives us the flexibility
    to change the implementation later, such as by spawning 
    additional worker threads if the task takes too long.
    """
    for player_key in stale_games_dict:
        __send_email(player_key, stale_games_dict[player_key])

def __send_email(player_key, game_list):
    app_id = app_identity.get_application_id()
    player = player_key.get()
    # Getting the full model here so we can add an opt-out flag later
    subject = "Pending Liar's Dice games"
    game_list_str = "\n".join([str(x) for x in game_list])
    body = "You have the following pending games:\n\n{}".format(
        game_list_str)
    mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
        player.email,
        subject,
        body)
    logging.info("Sent reminder email to {}".format(player.email))
