import logging
from random import randint
import models



class GameLogicError(Exception):
    """
    Top-level exception for all errors raised by our game logic layer.
    Calling methods can safely catch this if they don't care exactly
    why an action was rejected, since all methods here will throw
    a subclass of it.
    """
    pass

class InvalidMoveError(GameLogicError):
    """ The player attempted a move that was illegal according to the game rules. """
    pass

class GameRosterError(GameLogicError):
    """ There's something wrong with the game's internal player roster. """
    pass

class UnimplementedFeatureError(GameLogicError):
    """ This game feature hasn't been fully implemented yet. """
    pass


def initialize(game):
    """
    Performs all tasks required to prepare the game for play.
    Assumes that game.player_keys has already been populated.
    """
    keys = game.player_keys
    if not keys or len(keys) < 2:
        raise ValueError("player_keys has not been populated")
    game.active_player_key = keys[0]
    reset_scores(game)
    refill_hands(game)
    game.log = []
    game.log_entry("Started a new game.", timestamp=True)


def roll(faces=6):
    """ Simulates rolling a die with {n} faces. """
    return randint(1, faces)


STARTING_HAND_SIZE = 5
def roll_hand(hand_size=STARTING_HAND_SIZE):
    """ Rolls a new starting hand """
    return [roll() for x in range(hand_size)]

def reset_scores(game):
    """ Initializes the game's scores array so it can be incremented later. """
    game.scores = {x: 0 for x in game.player_keys}

def refill_hands(game):
    """ Rolls a new starting hand for all players in the game (new round). """
    game.reset_high_bid()
    game.dice = {x: roll_hand() for x in game.player_keys}

def reroll_hands(game):
    """ Rerolls all player hands, -without- replacing missing die (new turn) """
    game.reset_high_bid()
    game.dice = {x: roll_hand(hand_size=len(game.dice[x])) for x in game.player_keys}

BID_COUNTS = range(1, STARTING_HAND_SIZE + 1)
BID_RANKS = range(1, 7)
def place_bid(game, new_bid):
    """
    The active player's (possibly fraudulent) assertion that they have at least
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
        __do_place_bid(game, new_bid)
    elif new_bid.count > old_bid.count:
        __do_place_bid(game, new_bid)
    elif new_bid.count == old_bid.count and new_bid.rank > old_bid.rank:
        __do_place_bid(game, new_bid)
    else:
        raise InvalidMoveError("Illegal bid")

def __do_place_bid(game, new_bid):
    """
    Error checks passed, now actually commit the bid.
    """
    game.log_entry("{} placed the bid {}x{}".format(
        game.active_player_email(), new_bid.count, new_bid.rank),
        timestamp=True)
    game.high_bid = new_bid
    game.high_bidder_key = game.active_player_key
    assign_next_player(game)
    game.put()

def call_bluff(game):
    """
    If the high bid was a bluff, the high bidder removes one die.
    Otherwise, the active player removes a die.
    """
    if not (game.high_bid and game.high_bidder_key):
        raise InvalidMoveError("There are no standing bids")

    game.log_entry("{} called a bluff".format(
        game.active_player_email()),
        timestamp=True)
    actual_count = get_count(game, game.high_bidder_key, game.high_bid.rank)
    game.log_entry("{}'s actual hand was {}".format(
        game.high_bidder_email(),
        game.dice[game.high_bidder_key]))
    if actual_count < game.high_bid.count:
        game.log_entry("Correct!  {} loses a die".format(
            game.high_bidder_email()))
        remove_die(game, game.high_bidder_key)
    else:
        game.log_entry("Incorrect!  {} loses a die".format(
            game.active_player_email()))
        remove_die(game, game.active_player_key)
    turn_complete(game)
    assign_next_player(game)
    game.put()

def call_spot_on(game):
    """
    If the high bidder has exactly {count} dice of face {rank},
    everyone except the active player removes a die.
    Otherwise, the active player removes a die.
    """
    if not (game.high_bid and game.high_bidder_key):
        raise InvalidMoveError("There are no standing bids")

    game.log_entry("{} called spot on".format(
        game.active_player_email()),
        timestamp=True)
    actual_count = get_count(game, game.high_bidder_key, game.high_bid.rank)
    game.log_entry("{}'s actual hand was {}".format(
        game.high_bidder_email(),
        game.dice[game.high_bidder_key]))
    if actual_count == game.high_bid.count:
        game.log_entry("Correct!  Everyone else loses a die")
        for pk in game.player_keys:
            if pk != game.active_player_key:
                remove_die(game, pk)
    else:
        game.log_entry("Incorrect!  {} loses a die".format(
            game.active_player_email()))
        remove_die(game, game.active_player_key)
    turn_complete(game)
    assign_next_player(game)
    game.put()


def turn_complete(game):
    living_player_keys = get_living_player_keys(game)
    if len(living_player_keys) == 1:
        round_complete(game, living_player_keys[0])
    else:
        game.log_entry("Turn complete, rerolling hands")
        reroll_hands(game)

def get_living_player_keys(game):
    return [x for x in game.dice if game.dice[x]]

POINTS_TO_WIN = 2
def round_complete(game, winner_key):
    game.scores[winner_key] += 1
    if game.scores[winner_key] >= POINTS_TO_WIN:
        game_complete(game, winner_key)
    else:
        game.log_entry("Round complete, {} gains a point ({} -> {})".format(
            models.User.email_from_key(winner_key),
            game.scores[winner_key] - 1,
            game.scores[winner_key]))
        game.log_entry("Reloading player hands")
        refill_hands(game)


def game_complete(game, winner_key):
    game.log_entry("Game over, {} wins!".format(
        models.User.email_from_key(winner_key)))
    game.winner_key = winner_key
    game.active = False

def get_count(game, player_key, rank):
    """
    Count the number of dice in {player}'s hand in {game} whose faces
    are exactly equal to {rank}.
    """    
    hand = game.dice[player_key]
    return len([x for x in hand if x==rank])

def remove_die(game, player_key):
    """ Physically removes a die from a player's pool, so that subsequent rolls will be weaker. """
    del game.dice[player_key][0]

def assign_next_player(game):
    """
    Someone has made a bid; move the game along by selecting
    the new active player.
    """
    new_key = __choose_next_player(game)
    game.active_player_key = new_key
    game.log_entry("It is now {}'s turn".format(game.active_player_email()))



def __choose_next_player(game):
    """ 
    Traverse the full player list, starting with the active player.
    Return the first key we find that's still a living_player.
    """
    living_player_keys = get_living_player_keys(game)
    lp_count = len(living_player_keys)
    if lp_count < 1:
        raise GameRosterError("Tried to pick a new active player, but no one is still alive")
    if lp_count == 1:
        return living_player_keys[0]

    # There's more than one player still in the game, so we need to do a full traversal
    all_player_keys = __reslice_array(game.active_player_key, game.player_keys)
    for i in all_player_keys:
        if (i != game.active_player_key) and (i in living_player_keys):
            return i

    # A match should have been found if all our preconditions were met, throw an error
    raise GameRosterError("Unable to choose next player")


def __reslice_array(target_key, all_keys):
    """
    Build a new list consising of two concatenated slices:
      1. Everyone including + after the target key
      2. Everyone before the target key
    """
    count = len(all_keys)
    i = all_keys.index(target_key)
    slice1 = all_keys[i: count]
    slice2 = all_keys[0:i]
    output = slice1 + slice2
    return output
