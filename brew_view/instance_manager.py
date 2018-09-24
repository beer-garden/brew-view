import logging
import random
import string
from datetime import datetime

import brew_view
from bg_utils.fields import StatusInfo
from bg_utils.models import System
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.pika import get_routing_key, get_routing_keys

logger = logging.getLogger(__name__)


async def initialize(instance):
    """Initializes an instance.

    :param instance: The instance
    :return: QueueInformation object describing message queue for this system
    """
    system = System.objects.get(instances__contains=instance)

    logger.info("Initializing instance %s[%s]-%s",
                system.name, instance.name, system.version)

    routing_words = [system.name, system.version, instance.name]
    req_name = get_routing_key(*routing_words)
    req_args = {'durable': True, 'arguments': {'x-max-priority': 1}}
    req_queue = brew_view.clients['pika'].setup_queue(
        req_name, req_args, [req_name])

    routing_words.append(''.join(random.choice(
        string.ascii_lowercase + string.digits) for _ in range(10)))
    admin_keys = get_routing_keys(*routing_words, is_admin=True)
    admin_args = {'auto_delete': True}
    admin_queue = brew_view.clients['pika'].setup_queue(
        admin_keys[-1], admin_args, admin_keys)

    connection = {
        'host': brew_view.config.web.public_fqdn,
        'port': brew_view.config.amq.connections.message.port,
        'user': brew_view.config.amq.connections.message.user,
        'password': brew_view.config.amq.connections.message.password,
        'virtual_host': brew_view.config.amq.virtual_host,
        'ssl': {
            'enabled': brew_view.config.amq.connections.message.ssl.enabled,
        },
    }

    instance.status = 'INITIALIZING'
    instance.status_info = StatusInfo(heartbeat=datetime.utcnow())
    instance.queue_type = 'rabbitmq'
    instance.queue_info = {
        'admin': admin_queue,
        'request': req_queue,
        'connection': connection,
    }
    instance.save()

    # Send a request to start to the plugin on the plugin's admin queue
    brew_view.clients['pika'].start(
        system=system.name, version=system.version, instance=instance.name)

    return BeerGardenSchemaParser.serialize_instance(instance, to_string=True)


async def start(instance):
    """Starts an instance.

    :param instance: The instance
    :return: None
    """
    system = System.objects.get(instances__contains=instance)

    brew_view.clients['pika'].start(
        system=system.name, version=system.version, instance=instance.name)

    return BeerGardenSchemaParser.serialize_instance(instance, to_string=True)


async def stop(instance):
    """Stops an instance.

    :param instance: The instance
    :return: None
    """
    system = System.objects.get(instances__contains=instance)

    brew_view.clients['pika'].stop(
        system=system.name, version=system.version, instance=instance.name)

    return BeerGardenSchemaParser.serialize_instance(instance, to_string=True)
