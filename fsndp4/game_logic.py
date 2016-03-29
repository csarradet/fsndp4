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
