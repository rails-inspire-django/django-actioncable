# README

This package provides Rails Action Cable support to Django Channels.

## Install

Please make sure [Django channels](https://channels.readthedocs.io/) is already working in Django project before installing this package.

```bash
$ pip install django-actioncable
```

In the `asgi.py`, we have code like this

```python
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from django_app.core import routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_app.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(), 
        "websocket": URLRouter(routing.urlpatterns)
    }
)
```

Notes:

1. The `websocket` protocol would be handled by `URLRouter(routing.urlpatterns)`

In the routing file, we add below code:

```python
from actioncable import ActionCableConsumer


urlpatterns = [
    path("cable", ActionCableConsumer.as_asgi()),
]
```

Notes:

1. So all the Websocket requests sent to `ws://localhost:8000/cable` would be handled by `ActionCableConsumer`
2. The `ActionCableConsumer` would then dispatch the request to the corresponding channel class.

We can add below code to the routing file to register the channel class.

```python
from actioncable import ActionCableConsumer, CableChannel, cable_channel_register


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
```

1. We create a `ChatChannel`, which inherits from the `CableChannel`. 
2. The `cable_channel_register` decorator would register the `ChatChannel` class to the `ActionCableConsumer`.
3. In the `subscribe` callback method, we get the room pk from the `self.params` dict and subscribe the channel to the group `chat_{pk}`. 
4. In the `unsubscribe` callback method, we unsubscribe the channel from the group.

## HTML

```html
<!DOCTYPE html>
<html>
<head>
  <title>ActionCable Example</title>
</head>
<body>
<div id="messages"></div>

<script src="https://cdn.jsdelivr.net/npm/@rails/actioncable@7.1.2/app/assets/javascripts/actioncable.js"></script>
<script>
  document.addEventListener("DOMContentLoaded", function () {
    // Create a consumer object to connect to the ActionCable server
    const cable = ActionCable.createConsumer();

    // Define a channel and its corresponding functions
    const channel = cable.subscriptions.create({channel: "ChatChannel", pk: "1"}, {
      connected() {
        console.log("Connected to the chat channel.");
      },

      disconnected() {
        console.log("Disconnected from the chat channel.");
      },

      received(data) {
        // Display the received message
        const messagesDiv = document.getElementById("messages");
        const messageDiv = document.createElement("div");
        messageDiv.innerText = data;
        messagesDiv.appendChild(messageDiv);
      }
    });
  });
</script>

</body>
</html>
```

Notes:

1. We use the `ActionCable.createConsumer()` to create a consumer object to connect to the ActionCable server.
2. The `channe` is `ChatChannel`, so the `ChatChannel` we just created will be used to handle the request.
3. In the client, we can pass room pk to the `ChatChannel` by `pk: "1"`, and in the backend we can get it in the `self.params`
4. In this case, the channel will `subscribe` to the `chat_1` group.

## Test

Launch Django shell, and run below code:

```python
from actioncable import cable_broadcast

cable_broadcast("chat_1", message="Hello World")
```

You should be able to see the message appear on the web page.

`cable_broadcast` is a wrapper of Django Channel `async_to_sync(channel_layer.group_send)` method call, we can use it in Django view or external process such as Celery worker.

The `message` value can also be Python dict, and in javascript we can get it in the `data` parameter of the `received` callback method.
