import pytest
from channels.testing import WebsocketCommunicator
from channels.layers import get_channel_layer
from actioncable import cable_channel_register, ActionCableConsumer, CableChannel, compact_encode_json


@cable_channel_register
class ChatChannel(CableChannel):

    def __init__(self, consumer: ActionCableConsumer, identifier_key, params=None):
        self.params = params if params else {}
        self.identifier_key = identifier_key
        self.consumer = consumer
        self.group_name = None

    async def subscribe(self):
        self.group_name = f"chat_{self.params['pk']}"
        await self.consumer.subscribe_group(self.group_name, self)

    async def unsubscribe(self):
        await self.consumer.unsubscribe_group(self.group_name, self)


@pytest.mark.asyncio
async def test_subscribe():
    communicator = WebsocketCommunicator(ActionCableConsumer.as_asgi(), "/cable", subprotocols=['actioncable-v1-json'])
    connected, subprotocol = await communicator.connect(timeout=10)
    assert connected
    response = await communicator.receive_json_from()
    assert response == {"type": "welcome"}

    # Subscribe
    group_name = "chat_1"

    subscribe_command = {
        "command": "subscribe",
        "identifier": compact_encode_json({
            "channel": ChatChannel.__name__,
            "pk": '1',
        })
    }

    await communicator.send_to(text_data=compact_encode_json(subscribe_command))
    response = await communicator.receive_json_from(timeout=10)
    assert response['type'] == 'confirm_subscription'

    # Message
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        group_name,
        {
            "type": "message",
            "group": group_name,
            "data": {
                "message": 'html_snippet',
            },
        },
    )

    response = await communicator.receive_json_from(timeout=5)
    assert response['message'] == 'html_snippet'

    # Unsubscribe
    subscribe_command = {
        "command": "unsubscribe",
        "identifier": compact_encode_json({
            "channel": ChatChannel.__name__,
            "pk": '1',
        })
    }

    await communicator.send_to(text_data=compact_encode_json(subscribe_command))

    # Message
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        group_name,
        {
            "type": "message",
            "group": group_name,
            "data": {
                "message": 'html_snippet',
            },
        },
    )

    assert await communicator.receive_nothing() is True

    # Close
    await communicator.disconnect()
