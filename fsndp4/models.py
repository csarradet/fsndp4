import logging

from google.appengine.ext import ndb


class User(ndb.Model):
    email = ndb.StringProperty(required=True)

    @staticmethod
    def get_or_create(email):
        instance = User.get_by_id(email)
        if not instance:
            instance = User(id=email)
            instance.put()
            logging.info("Created new user: {}".format(email))
        return instance


class Game(ndb.Model):
    players = ndb.KeyProperty(required=True, kind="User", repeated=True)
    scores = ndb.PickleProperty(required=True)

    @staticmethod
    def create(players):
        """ Players should be an array of User instances """
        game = Game()
        game.scores = {}
        for p in players:
            game.set_score(p, 0)
        game.put()
        return game

    def set_score(self, player, score):
        self.scores[player.email] = score

    def add_point(self, player):
        self.scores[player.email] += 1

    def sub_point(self, player):
        self.scores[player.email] -= 1
