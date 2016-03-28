import logging

from google.appengine.ext import ndb


class User(ndb.Model):
    email = ndb.StringProperty(required=True)
    is_admin = ndb.BooleanProperty(default=False)

    # The canonical way to uniquely access a user is assumed
    # to be their email address; other modules should either
    # call this method to create a full User object (if
    # peripheral info is needed) or simply use the raw email
    # address strings (if we only need to identify the user,
    # avoiding a database hit).
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



class Game(ndb.Model):
    # Contains the canonical list of all players in the game (keys)
    # along with their current scores (values).
    scores = ndb.PickleProperty(required=True)

    @staticmethod
    def create(players):
        """ Players should be an array of email address strings """
        game = Game()
        game.scores = {}
        for p in players:
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


