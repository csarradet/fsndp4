from functools import wraps
import logging

import endpoints
from google.appengine.api import oauth
from google.appengine.ext import ndb
from protorpc import messages, message_types, remote

import game_logic
from game_logic import GameLogicError
from models import User, Game, Bid


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

class DiceMessage(messages.Message):
    die_rolls = messages.IntegerField(1, repeated=True)

class BidMessage(messages.Message):
    count = messages.IntegerField(1, required=True)
    rank = messages.IntegerField(2, required=True)

class GameIdMessage(messages.Message):
    value = messages.IntegerField(1, required=True)

class GameMessage(messages.Message):
    """ Only includes info that should be visible to the active player """
    score_messages = messages.MessageField(ScoreMessage, 1, repeated=True)
    active_player = messages.MessageField(UserMessage, 2, required=True)
    active_player_hand = messages.MessageField(DiceMessage, 3, required=True)
    high_bidder = messages.MessageField(UserMessage, 4)
    high_bid = messages.MessageField(BidMessage, 5)
    game_id = messages.MessageField(GameIdMessage, 6, required=True)

class GameCollection(messages.Message):
    game_messages = messages.MessageField(GameMessage, 1, repeated=True)



# Helper methods for message creation
def create_user_message(email_str):
    if not email_str:
        return None
    inst = UserMessage()
    inst.email = email_str
    return inst

def create_score_message(email_str, score):
    if not email_str and score:
        return None
    inst = ScoreMessage()
    inst.user = create_user_message(email_str)
    inst.score = int(score)
    return inst

def create_dice_message(int_list):
    if not int_list:
        return None
    inst = DiceMessage()
    inst.die_rolls = [int(x) for x in int_list]
    return inst

def create_bid_message(count, rank):
    if not count and rank:
        return None
    inst = BidMessage()
    inst.count = int(count)
    inst.rank = int(rank)
    return inst

def create_game_id_message(gid):
    inst = GameIdMessage()
    inst.value = int(gid)
    return inst

# Helper methods for converting models into messages
def user_to_message(user_model):
    return create_user_message(user_model.email)

def game_to_message(game_model):
    inst = GameMessage()

    # Game ID is public, and will be needed to post moves
    raw_id = game_model.key.id()
    inst.game_id = create_game_id_message(raw_id)

    # Scores are public info    
    inst.score_messages = []
    for key in game_model.player_keys:
        email = User.email_from_key(key)
        score_message = create_score_message(
            email, game_model.scores[key])
        inst.score_messages.append(score_message)

    # The active player's hand (and only *their* hand) is public info
    active_player_email = User.email_from_key(
        game_model.active_player_key)
    inst.active_player = create_user_message(active_player_email)
    inst.active_player_hand = create_dice_message(
        game_model.dice[game_model.active_player_key])

    # The high bid/bidder are public info
    hbkey = game_model.high_bidder_key
    if hbkey:    
        high_bidder_email = User.email_from_key(
            game_model.high_bidder_key)
        inst.high_bidder = create_user_message(high_bidder_email)
    else:
        inst.high_bidder = None

    hb = game_model.high_bid
    if hb:
        inst.high_bid = create_bid_message(hb.count, hb.rank)
    else:
        inst.high_bid = None

    return inst


# API definitions
@endpoints.api(name='liars_dice',
        version='v1',
        description="Liar's Dice API",
        allowed_client_ids=(endpoints.API_EXPLORER_CLIENT_ID,),
        )
class LiarsDiceApi(remote.Service):

    # Define API method decorators.  First, the basic ones with no prerequisites:    
    def login_required(func):
        """
        Requires that the API user be logged in before calling a method.
        Saves their User instance as a current_user_model kwarg.
        (all decorated methods should be aware of **kwargs)
        """
        @wraps(func)
        def login_required_dec(*args, **kwargs):
            current_user = endpoints.get_current_user()
            if current_user is None:
                raise endpoints.UnauthorizedException('Invalid token')
            current_user_model = User.get_or_create(current_user.email())
            kwargs["current_user_model"] = current_user_model
            return func(*args, **kwargs)
        return login_required_dec

    def game_required(func):
        """
        Requires that a valid game_id is provided (typically as a path variable).
        Saves the instance as a game_model kwarg.
        """            
        @wraps(func)
        def game_required_dec(self, request, *args, **kwargs):
            game_model = Game.get_by_id(request.game_id)
            if not game_model:
                raise endpoints.NotFoundException()
            kwargs["game_model"] = game_model
            return func(self, request, *args, **kwargs)
        return game_required_dec

    # And now advanced decorators that filter down the list of allowed users:
    def admin_only(func):
        """ 
        Prereq: function must already be decorated with @login_required.
        Requires that the API user be flagged as an admin in the datastore.
        """
        @wraps(func)
        def admin_only_dec(*args, **kwargs):
            user = kwargs["current_user_model"]
            if not (user and user.is_admin):
                raise endpoints.ForbiddenException('You must be an admin to perform that action')
            return func(*args, **kwargs)
        return admin_only_dec

    def active_player_only(func):
        """
        Prereq: @login_required AND @game_required.
        Errors out if the current user isn't the game's "active player".
        """
        @wraps(func)
        def active_player_only_dec(*args, **kwargs):
            game = kwargs["game_model"]
            current_user = kwargs["current_user_model"]
            if not current_user.key == game.active_player_key:
                raise endpoints.ForbiddenException('Only the active player can perform that action')
            return func(*args, **kwargs)
        return active_player_only_dec

    def enrolled_player_only(func):
        """
        Prereq: @login_required AND @game_required.
        Errors out if the current user isn't in the game's user list.
        """
        @wraps(func)
        def enrolled_player_only_dec(*args, **kwargs):
            game = kwargs["game_model"]
            current_user = kwargs["current_user_model"]
            if not current_user.key in game.player_keys:
                raise endpoints.ForbiddenException('Only an enrolled player can perform that action')
            return func(*args, **kwargs)
        return enrolled_player_only_dec



    # Define API methods
    @endpoints.method(message_types.VoidMessage,
            message_types.VoidMessage,
            http_method="POST",
            path="enroll_user",
            name="users.enroll")
    @login_required
    def enroll_user(self, request, **kwargs):
        """
        Create a new user record in the DB for the logged in user unless one already exists.
        """
        # The decorator does all the work here, no need for anything else.
        return message_types.VoidMessage()


    @endpoints.method(message_types.VoidMessage,
            UserCollection,
            http_method="GET",
            path="users",
            name="users.list")
    @login_required
    @admin_only
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
    @login_required
    @admin_only
    def delete_users(self, request, **kwargs):
        """ Wipe all locally stored user info from the database """
        User.delete_all()
        return message_types.VoidMessage()


    @endpoints.method(message_types.VoidMessage,
            GameCollection,
            http_method="GET",
            path="games",
            name="games.list")
    @login_required
    @admin_only
    def list_games(self, request, **kwargs):
        """ List all active and completed games """
        response = GameCollection()
        response.game_messages = [game_to_message(x) for x in Game.get_all()]
        return response


    GAME_LOOKUP_RC = endpoints.ResourceContainer(
        message_types.VoidMessage,
        game_id=messages.IntegerField(1, required=True))
    @endpoints.method(GAME_LOOKUP_RC,
        GameMessage,
        http_method="GET",
        path="games/{game_id}",
        name="games.lookup")
    @login_required
    @game_required
    @active_player_only
    def lookup_game(self, request, **kwargs):
        """ Look up one particular active or completed game """
        return game_to_message(kwargs["game_model"])


    BID_POST_RC = endpoints.ResourceContainer(
        BidMessage,
        game_id=messages.IntegerField(1, required=True))
    @endpoints.method(BID_POST_RC,
        message_types.VoidMessage,
        http_method="POST",
        path="games/{game_id}/bids",
        name="games.bids.create")
    @login_required
    @game_required
    @active_player_only
    def place_bid(self, request, **kwargs):
        bidder_key = kwargs["current_user_model"].key
        game = kwargs["game_model"]
        new_bid = Bid()
        new_bid.count = request.count
        new_bid.rank = request.rank
        try:
            game_logic.place_bid(game, new_bid, bidder_key)
        except GameLogicError:
            logging.exception("Invalid action")
            raise endpoints.BadRequestException("Invalid action")
        return message_types.VoidMessage()    


    @endpoints.method(message_types.VoidMessage,
            message_types.VoidMessage,
            http_method="DELETE",
            path="games",
            name="games.delete")
    @login_required
    @admin_only
    def delete_games(self, request, **kwargs):
        """ Wipe all active and completed games from the database """
        Game.delete_all()
        return message_types.VoidMessage()


    @endpoints.method(UserCollection,
            GameIdMessage,
            http_method="POST",
            path="games",
            name="games.create")
    @login_required
    @admin_only
    def create_game(self, request, **kwargs):
        """ If the current user is an admin, create a new game containing the provided players """
        if not request.user_messages:
            raise endpoints.BadRequestException("You must specify which players will be participating in the game")
        player_emails = [x.email for x in request.user_messages]
        game = Game.create(player_emails)
        return create_game_id_message(game.key.id())



APP = endpoints.api_server([LiarsDiceApi])
