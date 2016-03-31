import datetime
import logging

from google.appengine.ext import ndb

import game_logic


class User(ndb.Model):
    """
    A person who has logged in with a Google account and interacted with our server in some way.
    """
    email = ndb.StringProperty(required=True)
    is_admin = ndb.BooleanProperty(default=False)

    @staticmethod
    def get_or_create(email):
        """
        Always use get_or_create instead of standing up your
        own instances to ensure that the IDs are generated
        consistently.
        """
        instance = User.get_by_id(email)
        if not instance:
            instance = User(id=email)
            instance.email = email
            instance.put()
            logging.info("Created new user: {}".format(email))
        return instance

    @staticmethod
    def get_all():
        return User.query().fetch(limit=None)

    @staticmethod
    def delete_all():
        keys = User.query().fetch(keys_only=True)
        ndb.delete_multi(keys)

    @staticmethod
    def email_from_key(user_key):
        """ Given a User key, return the email address associated with its instance """
        # We could get the user's email from the key itself, but
        # we want to make sure they actually exist in the DB.
        return user_key.get().email


class Bid(ndb.Model):
    """ 
    Usually just used as a structured property for Game.
    A bid is a (possibly fraudulent) assertion that a player's
    hand contains at least {count} dice whose face reads {rank}
    """
    count = ndb.IntegerProperty(required=True, indexed=False)
    rank = ndb.IntegerProperty(required=True, indexed=False)

    @staticmethod
    def create(count, rank):
        """ 
        Bids typically aren't stored in the DB on their own,
        so this function doesn't automatically put() the
        newly created instance.
        """
        inst = Bid()
        inst.count = count
        inst.rank = rank
        return inst


class Game(ndb.Model):
    """
    Encapsulates a game state, its participants, and all required scoring info.
    """
    # List of ndb keys for all players in this game
    player_keys = ndb.KeyProperty(kind=User, repeated=True)
    active_player_key = ndb.KeyProperty(kind=User, required=True)
    # Only populated when the game is over
    winner_key = ndb.KeyProperty(kind=User, default=None)
    # Key: a participanting player's key
    # Value: that player's current score
    scores = ndb.PickleProperty(required=True)
    # Key: same as above
    # Value: a list of integers representing the dice remaining
    #   in that player's hand (may be an empty list if
    #   the player has been eliminated)
    dice = ndb.PickleProperty(required=True)
    high_bidder_key = ndb.KeyProperty(
        kind=User, default=None, indexed=False)
    high_bid = ndb.StructuredProperty(
        Bid, default=None, indexed=False)
    log = ndb.StringProperty(repeated=True)
    active = ndb.BooleanProperty(required=True, default=True)
    updated = ndb.DateTimeProperty(required=True, auto_now=True)

    @staticmethod
    def create(player_emails):
        """ Players should be an array of email address strings """
        game = Game()
        player_keys = [User.get_or_create(x).key for x in player_emails]
        player_keys.sort()
        game.player_keys = player_keys
        game_logic.initialize(game)
        game.put()
        return game

    @staticmethod
    def get_all():
        return Game.query().fetch(limit=None)

    @staticmethod
    def get_pending(user_model):
        """ Get all games that are waiting for {user} to make a move """
        q = Game.query(
            Game.active == True, 
            Game.active_player_key == user_model.key)
        return q.fetch(limit=None)            

    @staticmethod
    def delete_all():
        keys = Game.query().fetch(keys_only=True)
        ndb.delete_multi(keys)

    # Typically, you should only timestamp the first log
    # entry in a player-server interaction
    def log_entry(self, text, timestamp=False):
        """ Saves an important event to the game's logfile """
        if timestamp:
            self.log.append("At time {}:".format(
                datetime.datetime.now()))
        self.log.append(text)

    # Convenience methods to help clean up game_logic code
    def active_player_email(self):
        return User.email_from_key(self.active_player_key)

    def high_bidder_email(self):
        return User.email_from_key(self.high_bidder_key)

    def reset_high_bid(self):
        self.high_bid = None
        self.high_bidder_key = None


