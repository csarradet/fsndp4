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


# Endpoints message classes that correspond to our models
class UserMessage(messages.Message):
    email = messages.StringField(1, required=True)

class UserCollection(messages.Message):
    user_messages = messages.MessageField(UserMessage, 1, repeated=True)

class ScoreMessage(messages.Message):
    user = messages.MessageField(UserMessage, 1, required=True)
    score = messages.IntegerField(2, required=True)

class GameMessage(messages.Message):
    score_messages = messages.MessageField(ScoreMessage, 1, repeated=True)

class GameCollection(messages.Message):
    game_messages = messages.MessageField(GameMessage, 1, repeated=True)


# Helper methods for message creation
def create_user_message(email_str):
    inst = UserMessage()
    inst.email = email_str
    return inst

def create_score_message(email_str, score):
    inst = ScoreMessage()
    inst.user = create_user_message(email_str)
    inst.score = int(score)
    return inst

# Helper methods for converting models into messages
def user_to_message(user_model):
    return create_user_message(user_model.email)

def game_to_message(game_model):
    inst = GameMessage()
    inst.score_messages = []
    for key in game_model.player_keys:
        email = User.email_from_key(key)
        score_message = create_score_message(
            email, game_model.scores[key])
        inst.score_messages.append(score_message)
    return inst


# API definitions
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
            message_types.VoidMessage,
            http_method="POST",
            path="enroll_user",
            name="users.enroll")
    @admin_only
    def enroll_user(self, request):
        """
        Create a new user record in the DB for the logged in user unless one already exists.
        """
        # The admin_only decorator does all the work here, no need for anything else.
        return message_types.VoidMessage()


    @endpoints.method(message_types.VoidMessage,
            UserCollection,
            http_method="GET",
            path="users",
            name="users.list")
    def list_users(self, request):
        """ List all users that have ever interacted with the system """
        response = UserCollection()
        response.user_messages = [user_to_message(x) for x in User.get_all()]
        return response


    @endpoints.method(message_types.VoidMessage,
            message_types.VoidMessage,
            http_method="DELETE",
            path="users",
            name="users.delete")
    @admin_only
    def delete_users(self, request):
        """ Wipe all locally stored user info from the database """
        User.delete_all()
        return message_types.VoidMessage()





    @endpoints.method(message_types.VoidMessage,
            GameCollection,
            http_method="GET",
            path="games",
            name="games.list")
    def list_games(self, request):
        """ List all active and completed games """
        response = GameCollection()
        response.game_messages = [game_to_message(x) for x in Game.get_all()]
        return response


    @endpoints.method(message_types.VoidMessage,
            message_types.VoidMessage,
            http_method="DELETE",
            path="games",
            name="games.delete")
    @admin_only
    def delete_games(self, request):
        """ Wipe all active and completed games from the database """
        Game.delete_all()
        return message_types.VoidMessage()


    @endpoints.method(UserCollection,
            GameMessage,
            http_method="POST",
            path="games",
            name="games.create")
    @admin_only
    def create_game(self, request):
        """ If the current user is an admin, create a new game containing the provided players """
        if not request.user_messages:
            raise endpoints.BadRequestException("You must specify which players will be participating in the game")
        player_emails = [x.email for x in request.user_messages]
        game = Game.create(player_emails)
        return game_to_message(game)



APP = endpoints.api_server([LiarsDiceApi])
