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
    return randint(1,faces)


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
    bidder_email = models.User.email_from_key(bidder_key)
    game.log.append("{}: {} placed the bid {}x{}".format(
        datetime.datetime.now(), bidder_email,
        new_bid.count, new_bid.rank))
    # game.high_bid.count = new_bid.count
    # game.high_bid.rank = new_bid.rank
    game.high_bid = new_bid
    game.high_bidder_key = bidder_key
    next_player(game)
    game.put()

def call_bluff(game):
    """
    If the high bid was a bluff, the high bidder removes one die.
    Otherwise, the active player removes a die.
    """
    pass

def call_spot_on(game):
    """
    If the high bidder has exactly {count} dice of face {rank},
    everyone except the active player removes a die.
    Otherwise, the active player removes a die.
    """
    pass

def remove_die(game, player):
    """
    When a player's last die is removed, they're eliminated from
    this round.  Check to see if there are still active players.
    """
    pass

def next_player(game):
    """
    Someone has taken an action; move the game along by selecting
    the new active player.
    """
    pass
