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
    reset_scores(game)
    refill_hands(game)
    game.log = []
    game.log_entry("Started a new game.", timestamp=True)


def roll(faces=6):
    return randint(1, faces + 1)


STARTING_HAND_SIZE = 5
def roll_hand(hand_size=STARTING_HAND_SIZE):
    return [roll() for x in range(hand_size)]

def reset_scores(game):
    game.scores = {x: 0 for x in game.player_keys}

def refill_hands(game):
    game.reset_high_bid()
    game.dice = {x: roll_hand() for x in game.player_keys}

def reroll_hands(game):
    game.reset_high_bid()
    game.dice = {x: roll_hand(hand_size=len(game.dice[x])) for x in game.player_keys}

BID_COUNTS = range(1, STARTING_HAND_SIZE + 1)
BID_RANKS = range(1, 7)
def place_bid(game, new_bid, bidder_key):
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
        __do_place_bid(game, new_bid, bidder_key)
    elif new_bid.count > old_bid.count:
        __do_place_bid(game, new_bid, bidder_key)
    elif new_bid.count == old_bid.count and new_bid.rank > old_bid.rank:
        __do_place_bid(game, new_bid, bidder_key)
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
    game.log_entry("It is now {}'s turn".format(game.active_player_email()))
    game.put()

def call_bluff(game):
    """
    If the high bid was a bluff, the high bidder removes one die.
    Otherwise, the active player removes a die.
    """
    if not game.high_bid and game.high_bidder_key:
        raise InvalidMoveError("There are no standing bids")

    game.log_entry("{} called a bluff".format(
        game.active_player_email()),
        timestamp=True)
    actual_count = count_hand(game, game.high_bidder_key, game.high_bid.rank)
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
    game.put()

def call_spot_on(game):
    """
    If the high bidder has exactly {count} dice of face {rank},
    everyone except the active player removes a die.
    Otherwise, the active player removes a die.
    """
    if not game.high_bid and game.high_bidder_key:
        raise InvalidMoveError("There are no standing bids")

    game.log_entry("{} called spot on".format(
        game.active_player_email()),
        timestamp=True)
    actual_count = count_hand(game, game.high_bidder_key, game.high_bid.rank)
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
    game.put()


def turn_complete(game):
    living_player_keys = [x for x in game.dice if game.dice[x]]
    if len(living_player_keys) == 1:
        round_complete(game, winner=living_player_keys[0])
    else:
        game.log_entry("Turn complete, rerolling hands")
        reroll_hands(game)

POINTS_TO_WIN = 5
def round_complete(game, winner_key):
    game.scores[winner_key] += 1
    if game.scores[winner_key] >= POINTS_TO_WIN:
        game_complete(game, winner_key)
    else:
        game.log_entry("Round complete, {} gains a point ({} -> {})".format(
            models.User.email_from_key(winner_key)))
        game.log_entry("Reloading player hands")
        refill_hands(game)


def game_complete(game, winner_key):
    # TODO: flag the game as inactive
    game.log_entry("Game over, {} wins!".format(
        models.User.email_from_key(winner_key)))

def get_count(game, player_key, rank):
    """
    Count the number of dice in {player}'s hand in {game} whose faces
    are exactly equal to {rank}.
    """    
    hand = game.dice[player_key]
    return len([x for x in hand if x==rank])

def remove_die(game, player_key):
    del game.dice[player_key][0]

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


