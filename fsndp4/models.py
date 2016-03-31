import datetime
import logging

from google.appengine.ext import ndb

import game_logic


class User(ndb.Model):
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
        # We could get the user's email from the key itself, but
        # we want to make sure they actually exist in the DB.
        return user_key.get().email


class Bid(ndb.Model):
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
    # List of ndb keys for all players in this game
    player_keys = ndb.KeyProperty(kind=User, repeated=True)
    active_player_key = ndb.KeyProperty(kind=User, required=True)
    # Key: a participanting player's key
    # Value: that player's current score
    scores = ndb.PickleProperty(required=True)
    # Key: same as above
    # Value: a list of integers representing the dice remaining
    #   in that player's hand (may be an empty list if
    #   the player has been eliminated)
    dice = ndb.PickleProperty(required=True)
    high_bidder_key = ndb.KeyProperty(kind=User, default=None)
    high_bid = ndb.StructuredProperty(Bid, default=None)
    log = ndb.StringProperty(repeated=True)
    active = ndb.BooleanProperty(required=True, default=True)

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
        if timestamp:
            self.log.append("At time {}:".format(
                datetime.datetime.now()))
        self.log.append(text)

    def active_player_email(self):
        return User.email_from_key(self.active_player_key)

    def high_bidder_email(self):
        return User.email_from_key(self.high_bidder_key)

    def reset_high_bid(self):
        self.high_bid = None
        self.high_bidder_key = None


