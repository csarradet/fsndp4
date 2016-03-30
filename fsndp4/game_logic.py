import datetime
from random import randint
import models



class GameLogicError(Exception):
    """
    Top-level exception for all errors raised by our game logic layer.
    Calling methods can safely catch this if they don't care exactly
    why an action was rejected.
    """
    pass

class InvalidMoveError(GameLogicError):
    """ 
    The player attempted a move that was illegal according to the game rules. 
    """
    pass

class GameRosterError(GameLogicError):
    """
    There's something wrong with the game's internal player roster.
    """
    pass

class UnimplementedFeatureError(GameLogicError):
    """
    This game feature hasn't been fully implemented yet.
    """
    pass


def initialize(game):
    """
    Performs all tasks required to prepare the game for play.
    Assumes that game.player_keys has already been populated.
    """
    keys = game.player_keys
    if not keys:
        raise ValueError("player_keys has noot been populated")
    game.active_player_key = keys[0]
    game.scores = {x: 0 for x in keys}
    game.dice = {x: roll_hand() for x in keys}
    game.log = ["{}: Started a new game.  Opening hands:{}".format(
        datetime.datetime.now(), game.dice)]


def roll(faces=6):
    return randint(1, faces + 1)


STARTING_HAND_SIZE = 5
def roll_hand(hand_size=STARTING_HAND_SIZE):
    return [roll() for x in range(hand_size)]


BID_COUNTS = range(1, STARTING_HAND_SIZE + 1)
BID_RANKS = range(1, 7)
def place_bid(game, new_bid, bidder_key):
    """
    A player's (possibly false) assertion that they have at least
    {count} dice showing the face {rank}.

    If no bids exist, any physically possible bid is valid.

    A new bid must meet at least one of these criteria:
      - new_count > old_count
      - new_count == old_count AND new_rank > old_rank
    """
    if new_bid.count not in BID_COUNTS:
        raise InvalidMoveError("Invalid bid count")
    if new_bid.rank not in BID_RANKS:
        raise InvalidMoveError("Invalid bid rank")

    old_bid = game.high_bid

    if not old_bid:
        __do_place_bid(game, new_bid, bidder_key)
    elif new_bid.count > old_bid.count:
        __do_place_bid(game, new_bid, bidder_key)
    elif new_bid.count == old_bid.count and new_bid.rank > old_bid.rank:
        __do_place_bid(game, new_bid, bidder_key)
    else:
        raise InvalidMoveError("Illegal bid")

def __do_place_bid(game, new_bid, bidder_key):
    """
    Error checks passed, now actually commit the bid.
    """
    bidder_email = models.User.email_from_key(bidder_key)
    game.log.append("{}: {} placed the bid {}x{}".format(
        datetime.datetime.now(), bidder_email,
        new_bid.count, new_bid.rank))
    game.high_bid = new_bid
    game.high_bidder_key = bidder_key
    assign_next_player(game)
    new_player_email = models.User.email_from_key(
        game.active_player_key)
    game.log.append("{}: It is now {}'s turn".format(
        datetime.datetime.now(), new_player_email))
    game.put()

def call_bluff(game):
    """
    If the high bid was a bluff, the high bidder removes one die.
    Otherwise, the active player removes a die.
    """
    raise UnimplementedFeatureError("Not yet implemented")

def call_spot_on(game):
    """
    If the high bidder has exactly {count} dice of face {rank},
    everyone except the active player removes a die.
    Otherwise, the active player removes a die.
    """
    raise UnimplementedFeatureError("Not yet implemented")

def remove_die(game, player):
    """
    When a player's last die is removed, they're eliminated from
    this round.  Check to see if there are still active players.
    """
    raise UnimplementedFeatureError("Not yet implemented")

def assign_next_player(game):
    """
    Someone has taken an action; move the game along by selecting
    the new active player.
    """
    new_key = __choose_next_player(game)
    game.active_player_key = new_key


def __choose_next_player(game):
    # Concatenate the player list against itself to catch the case
    # where a player is last in the list.

    # TODO: Add check for player's dice count
    iter_players = game.player_keys + game.player_keys
    curr_key = game.active_player_key
    if curr_key not in iter_players:
        raise GameRosterError(
            "Active player is not enrolled for game {}".format(game.key))
    pick_next = False
    for i in iter_players:
        if pick_next:
            return i
        if curr_key == i:
            pick_next = True
    raise AssertionError("Unable to choose next player")


