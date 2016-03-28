import logging

import endpoints
from google.appengine.api import oauth
from google.appengine.ext import ndb
from protorpc import messages, message_types, remote

from models import User, Game



def create_user_message(email_str):
    inst = UserMessage()
    inst.email = email_str
    return inst

def user_to_message(user_model):
    return create_user_message(user_model.email)

class UserMessage(messages.Message):
    email = messages.StringField(1)

class UserCollection(messages.Message):
    user_messages = messages.MessageField(UserMessage, 1, repeated=True)



@endpoints.api(name='liars_dice',
        version='v1',
        description="Liar's Dice API",
        allowed_client_ids=(endpoints.API_EXPLORER_CLIENT_ID,),
        )
class LiarsDiceApi(remote.Service):

    @endpoints.method(message_types.VoidMessage,
            UserCollection,
            http_method="GET")
    def list_users(self, request):
        user_messages = [user_to_message(x) for x in User.get_all()]
        response = UserCollection()
        response.user_messages = user_messages
        return response


    @endpoints.method(UserMessage,
            message_types.VoidMessage,
            http_method="POST")
    def create_user(self, request):
        current_user = endpoints.get_current_user()
        if current_user is None:
            raise endpoints.UnauthorizedException('Invalid token')
        current_user_model = User.get_or_create(current_user.email())
        if not current_user_model.is_admin:
            raise endpoints.ForbiddenException('You must be an admin to perform that action')


        inst = User()
        inst.email = request.email
        inst.put()
        return message_types.VoidMessage()



APP = endpoints.api_server([LiarsDiceApi])
