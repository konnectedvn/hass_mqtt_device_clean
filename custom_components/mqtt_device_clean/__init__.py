"""
Aim to remove all mqtt-discovery entities belong to a device in Hass
by clearing all related mqtt config topics.
Configuration:
To use the remove_mqtt_device component you will need to add the following to your
configuration.yaml file.
mqtt_device_clean:
"""
from homeassistant.core import callback
from homeassistant.components import mqtt
from homeassistant.components.mqtt import discovery, device_trigger
from homeassistant.helpers.entity import Entity
import logging
#import asyncio

# The domain of your component. Should be equal to the name of your component.
DOMAIN = "mqtt_device_clean"

# List of integration names (string) your integration depends upon.
DEPENDENCIES = ["mqtt"]

_LOGGER = logging.getLogger(__name__)

#CONF_TOPIC = 'discovery_topic'
DEFAULT_PREFIX = 'homeassistant'

SUPPORTED_COMPONENTS = discovery.SUPPORTED_COMPONENTS

DEVICE_ID = ''

async def async_setup(hass, config):
    """Set up the Remove MQTT Device component."""
    discovery_prefix = 'homeassistant'

    @callback
    async def async_device_message_received(msg) -> bool:
        """Process the received message."""
        topic = msg.topic
        retain = msg.retain
        payload = msg.payload

        if not retain or not payload or not topic:
            return False

        topic_trimmed = topic.replace(f"{discovery_prefix}/", "", 1)
        match = discovery.TOPIC_MATCHER.match(topic_trimmed)

        if not match:
            return False
        
        component, node_id, object_id = match.groups()

        discovery_id = " ".join((node_id, object_id)) if node_id else object_id
        
        if component is None:
            return False

        if component in SUPPORTED_COMPONENTS and DEVICE_ID in discovery_id:
            _LOGGER.info(
                "Component %s found at topic %s",
                component, topic,
            )
            # Publish with empty payload, qos: 0, retain: True
            hass.components.mqtt.async_publish(topic, "", 0, True)
            # Remove 
            await mqtt.device_trigger.async_device_removed(hass, DEVICE_ID)

        elif node_id == DEVICE_ID:
            _LOGGER.info(
                "Found unsupported device component: %s",
                component,
            )
        return True
        
    @callback
    async def remove_device_service(call):
        global discovery_topic
        global DEVICE_ID
        global NO_ENTITIES

        discovery_topic = config[DOMAIN].get("discovery_prefix") or DEFAULT_PREFIX
        discovery_topic += '/#'
        DEVICE_ID = call.data.get("device_id")
        
        if not DEVICE_ID.strip():
            _LOGGER.warning(
                "A blank device_id is not permitted!"
            )
            return

        # Subscribe our listener to discovery topic
        await hass.components.mqtt.async_subscribe(discovery_topic, async_device_message_received)
        
        # Wait 3 seconds
        #await asyncio.sleep(3)

        # Unsubscribe from discovery topic
        #await hass.components.mqtt.MQTT._async_unsubscribe(hass, discovery_topic)
        
    # Register our service with Home Assistant
    hass.services.async_register(DOMAIN, "apply", remove_device_service)
    
    # Return boolean to indicate that initialization was successfully.
    return True