import json
import time
import logging

from collections import defaultdict
import actioncable.registry
import sys
import os

import asyncio
from channels.generic.websocket import (
    AsyncJsonWebsocketConsumer,
)


if "pytest" in sys.argv[0] or "TOX_ENV_NAME" in os.environ:
    TEST_ENV = True
else:
    TEST_ENV = False


LOGGER = logging.getLogger(__name__)


def compact_encode_json(content):
    # compact encoding
    return json.dumps(content, separators=(",", ":"), sort_keys=True)


class ActionCableConsumer(AsyncJsonWebsocketConsumer):
    """
    Make Django Channels compatible with Rails ActionCable JS client
    """

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.ping_task = None
        # the channel name to channel_cable_class
        self.channel_cls_dict = actioncable.registry.registered_classes
        self.identifier_to_channel_instance_map = {}
        self.group_channel_instance_map = defaultdict(set)

    async def connect(self):
        await self.accept("actioncable-v1-json")
        await self.send(text_data='{"type": "welcome"}')

        if not TEST_ENV:
            # periodically send ping message to the client
            # if the client did not receive the ping message within X seconds, it will try reconnect
            loop = asyncio.get_event_loop()
            self.ping_task = loop.create_task(self.send_ping())

    async def disconnect(self, close_code):
        if not TEST_ENV:
            # Stop the ping task when disconnecting
            self.ping_task.cancel()

    async def send_ping(self):
        while True:
            ping_message = {"type": "ping", "message": int(time.time())}
            await self.send_json(ping_message)  # Send the ping message to the client
            await asyncio.sleep(5)  # Wait for 5 seconds

    async def receive_json(self, content, **kwargs):
        command = content.get("command", None)
        identifier_dict = json.loads(content["identifier"])
        unique_identifier_key = await self.encode_json(identifier_dict)

        # get or create channel instance for the identifier
        if unique_identifier_key in self.identifier_to_channel_instance_map:
            channel_instance = self.identifier_to_channel_instance_map[
                unique_identifier_key
            ]
        else:
            channel_cls = self.channel_cls_dict[identifier_dict.get("channel")]
            channel_instance = channel_cls(
                consumer=self,
                identifier_key=unique_identifier_key,
                params=identifier_dict,
            )
            self.identifier_to_channel_instance_map[unique_identifier_key] = (
                channel_instance
            )

        if command == "subscribe":
            await channel_instance.subscribe()
            await self.send_json(
                {
                    "identifier": await self.encode_json(identifier_dict),
                    "type": "confirm_subscription",
                }
            )
        elif command == "unsubscribe":
            await channel_instance.unsubscribe()
        elif command == "message":
            await channel_instance.on_message(content, **kwargs)

    async def action_cable_message(self, event):
        """Send Turbo Stream HTML message back to the client"""
        group_name = event["group"]

        if group_name in self.group_channel_instance_map:
            for channel_instance_unique_key in self.group_channel_instance_map[
                group_name
            ]:
                # send message to all cable channels which subscribe to this group
                cable_channel_instance = self.identifier_to_channel_instance_map[
                    channel_instance_unique_key
                ]
                await self.send_json(
                    {
                        "identifier": cable_channel_instance.identifier_key,
                        "message": event["message"],
                    }
                )
        else:
            LOGGER.warning(
                "Group name %s not found in group_channel_instance_map", group_name
            )

    async def subscribe_group(self, group_name, cable_channel_instance):
        await self.channel_layer.group_add(group_name, self.channel_name)
        self.group_channel_instance_map[group_name].add(
            cable_channel_instance.identifier_key
        )

    async def unsubscribe_group(self, group_name, cable_channel_instance):
        has_other_cable_channel_subscribe = False
        if group_name in self.group_channel_instance_map:
            subscribed_channel_instance_keys = self.group_channel_instance_map[
                group_name
            ]
            if (
                len(subscribed_channel_instance_keys) > 1
                and cable_channel_instance.identifier_key
                in subscribed_channel_instance_keys
            ):
                has_other_cable_channel_subscribe = True
            self.group_channel_instance_map[group_name].discard(
                cable_channel_instance.identifier_key
            )

        if not has_other_cable_channel_subscribe:
            # if there is no other cable channel subscribe to this group
            # then we can let the consumer leave the group entirely
            await self.channel_layer.group_discard(group_name, self.channel_name)

        try:
            del self.identifier_to_channel_instance_map[
                cable_channel_instance.identifier_key
            ]
        except KeyError:
            pass

    @classmethod
    async def encode_json(cls, content):
        return compact_encode_json(content)


class CableChannel:
    def __init__(self, consumer: ActionCableConsumer, identifier_key, params=None):
        raise NotImplementedError("Please implement subscribe method")

    async def subscribe(self):
        """
        callback to run when received subscribe command from the client
        """
        raise NotImplementedError("Please implement subscribe method")

    async def unsubscribe(self):
        """
        callback to run when received unsubscribe command from the client
        """
        raise NotImplementedError("Please implement unsubscribe method")

    async def on_message(self, content, **kwargs): ...
