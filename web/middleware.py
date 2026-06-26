# game/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import get_token
from django.contrib.auth import get_user_model
from uuid import UUID
from web import utils

User = get_user_model()

class AnonymousGameUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """This enables to create guest users wihtout a password.
        """
        if request.user.is_authenticated:
            return
        user_id = request.session.get("anonymous_user_id")
        try:
            if user_id:
                user = User.objects.get(pk=user_id)
            else:
                raise User.DoesNotExist
        except (User.DoesNotExist, ValueError):
            user = User.objects.create_user(
                username=utils.get_player_guest_name(),
                color=utils.get_random_color(),
                password=None
            )
            user.set_unusable_password()
            user.save()
            request.session["anonymous_user_id"] = str(user.id)
            
        get_token(request)  # ensures users have a crsf token
        request.user = user
