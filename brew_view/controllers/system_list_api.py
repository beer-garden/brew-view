import logging

from tornado.gen import coroutine
from tornado.locks import Lock

from bg_utils.models import System, Instance
from bg_utils.parser import BeerGardenSchemaParser
from brew_view.base_handler import BaseHandler
from brewtils.errors import ModelValidationError
from brewtils.models import Events
from brewtils.schemas import SystemSchema


class SystemListAPI(BaseHandler):

    parser = BeerGardenSchemaParser()
    logger = logging.getLogger(__name__)

    REQUEST_FIELDS = set(SystemSchema.get_attribute_names())

    # Need to ensure that Systems are updated atomically
    system_lock = Lock()

    def get(self):
        """
        ---
        summary: Retrieve all Systems
        parameters:
          - name: include_commands
            in: query
            required: false
            description: Include System's commands in the response
            type: boolean
            default: true
        responses:
          200:
            description: All Systems
            schema:
              type: array
              items:
                $ref: '#/definitions/System'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        query_set = System.objects.order_by(self.request.headers.get('order_by', 'name'))
        serialize_params = {'to_string': True, 'many': True}

        include_fields = set(self.request.headers.get_list('include_field'))
        exclude_fields = set(self.request.headers.get_list('exclude_field'))
        include_commands = self.get_query_argument('include_commands', None)

        if include_fields and exclude_fields:
            raise Exception('Headers "include_field" and "exclude_field" can'
                            'not exist on the same request')
        elif include_commands and (include_fields or exclude_fields):
            raise Exception('Headers "include_field" and "exclude_field" can'
                            'not be used with "include_commands"')
        elif include_fields:
            # include_fields = include_fields & self.REQUEST_FIELDS
            query_set = query_set.only(*include_fields)
        elif exclude_fields:
            exclude_fields = exclude_fields & self.REQUEST_FIELDS
            query_set = query_set.exclude(*exclude_fields)
            serialize_params['exclude'] = exclude_fields

        # Convert the legacy include_commands into a bool:
        if include_commands:
            include_commands = include_commands.lower() != 'false'

            if not include_commands:
                query_set = query_set.exclude('commands')
                serialize_params['include_commands'] = False

        # Need to use self.request.query_arguments to get ALL the query args
        # Once we know the name use get_query_argument to get the decoded value
        # TODO Handle multiple query arguments with the same key
        filter_params = {
            key: self.get_query_argument(key) for key in self.request.query_arguments
        }
        # TODO IN Python 3 views have set operations
        # query_set = query_set.order_by(self.request.headers.get('order_by', 'name'))

        result_set = query_set.filter(**filter_params)

        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(self.parser.serialize_system(result_set, **serialize_params))

    @coroutine
    def post(self):
        """
        ---
        summary: Create a new System or update an existing System
        description: If the System does not exist it will be created. If the System already exists
            it will be updated (assuming it passes validation).
        parameters:
          - name: system
            in: body
            description: The System definition to create / update
            schema:
              $ref: '#/definitions/System'
        responses:
          200:
            description: An existing System has been updated
            schema:
              $ref: '#/definitions/System'
          201:
            description: A new System has been created
            schema:
              $ref: '#/definitions/System'
          400:
            $ref: '#/definitions/400Error'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Systems
        """
        self.request.event.name = Events.SYSTEM_CREATED.name

        system_model = self.parser.parse_system(self.request.decoded_body, from_string=True)

        with (yield self.system_lock.acquire()):
            # See if we already have a system with this name + version
            existing_system = System.find_unique(system_model.name, system_model.version)

            if not existing_system:
                self.logger.debug("Creating a new system: %s" % system_model.name)
                saved_system, status_code = self._create_new_system(system_model)
            else:
                self.logger.debug("System %s already exists. Updating it." % system_model.name)
                self.request.event.name = Events.SYSTEM_UPDATED.name
                saved_system, status_code = self._update_existing_system(existing_system,
                                                                         system_model)

            saved_system.deep_save()

        self.request.event_extras = {'system': saved_system}

        self.set_status(status_code)
        self.write(self.parser.serialize_system(saved_system, to_string=False,
                                                include_commands=True))

    @staticmethod
    def _create_new_system(system_model):
        new_system = system_model

        # Assign a default 'main' instance if there aren't any instances and there can only be one
        if not new_system.instances or len(new_system.instances) == 0:
            if new_system.max_instances is None or new_system.max_instances == 1:
                new_system.instances = [Instance(name='default')]
                new_system.max_instances = 1
            else:
                raise ModelValidationError('Could not create system %s-%s: Systems with '
                                           'max_instances > 1 must also define their instances' %
                                           (system_model.name, system_model.version))
        else:
            if not new_system.max_instances:
                new_system.max_instances = len(new_system.instances)

        return new_system, 201

    @staticmethod
    def _update_existing_system(existing_system, system_model):
        # Raise an exception if commands already exist for this system and they differ from what's
        # already in the database in a significant way
        if existing_system.commands and 'dev' not in existing_system.version and \
                existing_system.has_different_commands(system_model.commands):
            raise ModelValidationError('System %s-%s already exists with different commands' %
                                       (system_model.name, system_model.version))
        else:
            existing_system.upsert_commands(system_model.commands)

        # Update instances
        if not system_model.instances or len(system_model.instances) == 0:
            system_model.instances = [Instance(name='default')]

        for attr in ['description', 'icon_name', 'display_name']:
            value = getattr(system_model, attr)

            # If we set an attribute on the model as None, mongoengine marks the attribute for
            # deletion. We want to prevent this, so we set it to an emtpy string.
            if value is None:
                setattr(existing_system, attr, "")
            else:
                setattr(existing_system, attr, value)

        # Update metadata
        new_metadata = system_model.metadata or {}
        existing_system.metadata.update(new_metadata)

        old_instances = [inst for inst in existing_system.instances
                         if system_model.has_instance(inst.name)]
        new_instances = [inst for inst in system_model.instances
                         if not existing_system.has_instance(inst.name)]
        existing_system.instances = old_instances + new_instances

        return existing_system, 200
