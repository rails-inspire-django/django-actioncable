import os
import pathlib


def pytest_configure():
    from django.conf import settings

    settings.configure(
        SECRET_KEY="seekret",
        DATABASES={
            "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "mem_db"},
        },
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [pathlib.Path(__file__).parent.absolute() / "templates"],
                "APP_DIRS": True,
                "OPTIONS": {
                    "debug": False,
                    "context_processors": [],
                    "builtins": [],
                    "libraries": {},
                },
            }
        ],
        INSTALLED_APPS=[
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.sites",
            "channels",
        ],
        CHANNEL_LAYERS={
            "default": {
                "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
                "CONFIG": {
                    "hosts": [os.getenv("CHANNEL_LAYERS", "redis://localhost:6379/0")],
                },
            },
        }
    )
