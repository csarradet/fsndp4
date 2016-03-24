from google.appengine.ext import ndb
from protorpc import messages, message_types, remote

from models import (
    User, UserMessage, MultiUserMessage, 
    Game
    )


@endpoints.api(name='liars_dice', version='v1')
class LiarsDiceApi(remote.Service):
    
    @endpoints.method(message_types.VoidMessage,
            MultiUserMessage,
            name="list_users",
            path="users",
            http_method="GET")
    def list_users(self, request):
        user_messages = [x.to_message() for x in User.get_all()]
        response = MultiUserMessage()
        response.emails = user_messages
        return response


api = endpoints.api_server(['liars_dice'])
