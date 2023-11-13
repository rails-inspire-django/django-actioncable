from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def cable_broadcast(group_name, data=None):
    data = data if data else {}
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "message",
            "group": group_name,
            "data": data,
        },
    )
