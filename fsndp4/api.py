from functools import wraps
import logging

import endpoints
from google.appengine.api import oauth
from google.appengine.ext import ndb
from protorpc import messages, message_types, remote

from models import User, Game


# Valid endpoints exceptions:
# endpoints.BadRequestException   HTTP 400
# endpoints.UnauthorizedException HTTP 401
# endpoints.ForbiddenException    HTTP 403
# endpoints.NotFoundException HTTP 404
# endpoints.InternalServerErrorException  HTTP 500


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

    def admin_only(func):
        """ Requires that the API user be logged in and flagged as an admin in the datastore """
        @wraps(func)
        def decorator(*args, **kwargs):
            current_user = endpoints.get_current_user()
            if current_user is None:
                raise endpoints.UnauthorizedException('Invalid token')
            current_user_model = User.get_or_create(current_user.email())
            if not current_user_model.is_admin:
                raise endpoints.ForbiddenException('You must be an admin to perform that action')
            return func(*args, **kwargs)

        return decorator


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
    @admin_only
    def create_user(self, request):
        inst = User()
        inst.email = request.email
        inst.put()
        return message_types.VoidMessage()



APP = endpoints.api_server([LiarsDiceApi])
