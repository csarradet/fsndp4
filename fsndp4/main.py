import webapp2

import api
import email_task


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """
        Send a reminder email to each User with a "stale" game.
        Called once daily using a cron job.
        """
        email_task.start()


APP = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
], debug=True)
