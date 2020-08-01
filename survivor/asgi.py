from channels.layers import get_channel_layer
import os
import django
from channels.routing import get_default_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "survivor.settings")
django.setup()
application = get_default_application()