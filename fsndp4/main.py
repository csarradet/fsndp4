import webapp2

import api
import email_task


class HelloWorld(webapp2.RequestHandler):
    def get(self):
        """ Just a splash page to make sure the app is running. """
        self.response.out.write("Hello world")


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """
        Send a reminder email to each User with a "stale" game.
        Called once daily using a cron job.
        """
        email_task.start()


WEB_APP = webapp2.WSGIApplication([
    ('/', HelloWorld),
    ('/crons/send_reminder', SendReminderEmail),
], debug=True)

API_APP = api.APP
