from google.appengine.api import mail, app_identity
import webapp2

import api

class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        for user in users:
            subject = 'This is a reminder!'
            body = 'Hello {}, try out Guess A Number!'.format(user.email)
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)

class HelloWorld(webapp2.RequestHandler):
    def get(self):
        self.response.out.write("Hello world")



WEB_APP = webapp2.WSGIApplication([
    ('/', HelloWorld),
    ('/crons/send_reminder', SendReminderEmail),
], debug=True)


API_APP = api.APP
