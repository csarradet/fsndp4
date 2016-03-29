import logging

from google.appengine.ext import ndb


class User(ndb.Model):
    email = ndb.StringProperty(required=True)
    is_admin = ndb.BooleanProperty(default=False)

    @staticmethod
    def get_or_create(email):
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
        # TODO: memcache
        return user_key.get().email


class Game(ndb.Model):
    # List of ndb keys for all players in this game
    player_keys = ndb.KeyProperty(kind=User, repeated=True)
    # Key: a participanting player's key
    # Value: that player's current score
    scores = ndb.PickleProperty(required=True)

    @staticmethod
    def create(player_emails):
        """ Players should be an array of email address strings """
        game = Game()
        game.player_keys = [User.get_or_create(x).key for x in player_emails]
        game.scores = {}
        for p in game.player_keys:
            game.set_score(p, 0)
        game.put()
        return game

    @staticmethod
    def get_all():
        return Game.query().fetch(limit=None)

    @staticmethod
    def delete_all():
        keys = Game.query().fetch(keys_only=True)
        ndb.delete_multi(keys)

    def set_score(self, player, score):
        self.scores[player] = score

    def add_point(self, player):
        self.scores[player] += 1

    def sub_point(self, player):
        self.scores[player] -= 1
