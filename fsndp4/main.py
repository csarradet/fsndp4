import webapp2

import api
import email_task
import standings_task


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """
        Send a reminder email to each User with a "stale" game.
        Called once daily using a cron job.
        """
        email_task.start()

class UpdatePlayerStandings(webapp2.RequestHandler):
    def get(self):
        """
        Updates the player leaderboards every night.
        """
        standings_task.start()


APP = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/crons/update_standings', UpdatePlayerStandings)
], debug=True)
