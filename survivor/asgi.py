from channels.layers import get_channel_layer
import os


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "survivor.settings")
channel_layer = get_channel_layer()