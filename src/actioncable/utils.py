from typing import Union
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def cable_broadcast(group_name: str, message: Union[str, dict]):
    """
    Rails: ActionCable.server.broadcast
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "action_cable_message",
            # should put group_name in the message, so the ActionCableConsumer can know which group this message sent to
            "group": group_name,
            "message": message,
        },
    )


async def async_cable_broadcast(group_name: str, message: Union[str, dict]):
    """
    Rails: ActionCable.server.broadcast
    """
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        group_name,
        {
            "type": "action_cable_message",
            # should put group_name in the message, so the ActionCableConsumer can know which group this message sent to
            "group": group_name,
            "message": message,
        },
    )
