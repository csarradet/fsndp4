from google.appengine.api import mail


# class SendReminderEmail(webapp2.RequestHandler):
#     def get(self):
#         """Send a reminder email to each User with an email about games.
#         Called every hour using a cron job"""
#         app_id = app_identity.get_application_id()
#         users = User.query(User.email != None)
#         for user in users:
#             subject = 'This is a reminder!'
#             body = 'Hello {}, try out Guess A Number!'.format(user.email)
#             # This will send test emails, the arguments to send_mail are:
#             # from, to, subject, body
#             mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
#                            user.email,
#                            subject,
#                            body)

def start():
    pass
