import logging

LOGGER = logging.getLogger(__name__)

registered_classes = {}


def cable_channel_register(cls):
    class_name = cls.__name__
    if class_name in registered_classes:
        logging.warning(f"Class '{class_name}' is already registered in cable_channel_register and will be overwritten")
    registered_classes[class_name] = cls
    return cls
