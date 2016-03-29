import datetime
from random import randint
import models


STARTING_HAND_SIZE = 5

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


def roll_hand(hand_size=STARTING_HAND_SIZE):
    return [roll() for x in range(hand_size)]


def place_bid(game, bid, bidder_email):
    """
    A player's (possibly false) assertion that they have at least
    {count} dice showing the face {rank}.

    If no bids exist, any physically possible bid is valid.

    A new bid must meet at least one of these criteria:
      - new_count > old_count
      - new_count == old_count AND new_rank > old_rank
    """    
    pass


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