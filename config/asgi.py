import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import re_path

from chat.consumers import ChatConsumer  
from chat.middleware import JWTAuthMiddlewareStack  # Ensure this import is correct

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AllowedHostsOriginValidator(
            JWTAuthMiddlewareStack(
                URLRouter([
                    re_path(r"ws/chat/(?P<room_name>[\w-]+)/$", ChatConsumer.as_asgi()),  # Allow hyphens
                ])
            )
        ),
    }
)

