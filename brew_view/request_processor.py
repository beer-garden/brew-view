import asyncio
import collections
import json
import logging
import re

import six
from builtins import str

import brew_view
from bg_utils.models import Choices, Request, System
from brewtils.choices import parse
from brewtils.errors import (
    ModelValidationError, RequestPublishException, TimeoutExceededError)

logger = logging.getLogger(__name__)


async def create_request(request, wait=False, timeout=None):
    """Validates and publishes a Reqeust

    Args:
        request:
        wait:
        timeout:

    Returns:
        None

    Raises:
        InvalidRequest: The Request is invalid in some way
        PublishException: Something went wrong publishing to RabbitMQ
    """
    # Validates the request based on what is in the database.
    # This includes the validation of the request parameters,
    # systems are there, commands are there etc.
    request = await RequestValidator().validate_request(request)
    request.save()

    if not brew_view.clients['pika'].publish_request(
            request,
            confirm=True,
            mandatory=True,
    ):
        raise RequestPublishException(
            "Error while publishing request to queue (%s[%s]-%s %s)" %
            (request.system, request.system_version, request.instance_name,
             request.command)
        )

    if wait:
        event = asyncio.Event()
        brew_view.request_map[str(request.id)] = event

        try:
            await asyncio.wait_for(
                event.wait(), timeout=int(timeout) if timeout else None)
        except asyncio.TimeoutError:
            raise TimeoutExceededError()

        request.reload()

    return request


class RequestValidator(object):

    logger = logging.getLogger(__name__)

    async def validate_request(self, request):
        """Validation to be called before you save a request from a user

        :param request: The request to validate
        """
        self.logger.debug("Validating request")

        system = self.get_and_validate_system(request)
        command = self.get_and_validate_command_for_system(request, system)

        request.parameters = await self.get_and_validate_parameters(request, command)

        return request

    def get_and_validate_system(self, request):
        """Ensure there is a system in the DB that corresponds to this Request.

        :param request: The request to validate
        :return: The system corresponding to this Request
        :raises ModelValidationError: There is no system that corresponds to this Request
        """
        system = System.find_unique(request.system, request.system_version)
        if system is None:
            raise ModelValidationError(
                "Could not find System named '%s' matching version '%s'" %
                (request.system, request.system_version))

        if request.instance_name not in system.instance_names:
            raise ModelValidationError(
                "Could not find instance with name '%s' in system '%s'" %
                (request.instance_name, system.name))

        self.logger.debug("Found System %s-%s" % (request.system, request.instance_name))
        return system

    def get_and_validate_command_for_system(self, request, system=None):
        """Ensure the System has a command with a name that matches this request.

        :param request: The request to validate
        :param system: Specifies a System to use. If None a system lookup will be attempted.
        :return: The database command
        :raises ValidationError: if the request or command is invalid
        """
        self.logger.debug("Getting and Validating Command for System")
        if system is None:
            self.logger.debug("No System was passed in")
            system = self.get_and_validate_system(request)

        if request.command is None:
            self.logger.error("Could not validate command because it was none")
            raise ModelValidationError("Could not validate command because it was None.")

        self.logger.debug("Looking through Command Names to find the Command Specified.")
        command_names = []
        for command in system.commands:
            if command.name == request.command:
                self.logger.debug("Found Command with name: %s" % request.command)

                if request.command_type is None:
                    request.command_type = command.command_type
                elif command.command_type != request.command_type:
                    self.logger.error("Command Type for Request was %s but the command "
                                      "specified the command_type as %s" %
                                      (request.command_type, command.command_type))
                    raise ModelValidationError(
                        "Command Type for Request was %s but the command specified "
                        "the type as %s" %
                        (request.command_type, command.command_type))

                if request.output_type is None:
                    request.output_type = command.output_type
                elif command.output_type != request.output_type:
                    self.logger.error("Output Type for Request was %s but the command specified "
                                      "the output_type as %s" %
                                      (request.output_type, command.output_type))
                    raise ModelValidationError(
                        "Output Type for Request was %s but the command specified "
                        "the type as %s" %
                        (request.output_type, command.output_type))

                return command

            command_names.append(command.name)

        self.logger.error("No Command with name: %s could be found. Valid Commands for %s "
                          "are: %s" % (request.command, system.name, command_names))
        raise ModelValidationError(
            "No Command with name: %s could be found. Valid Commands for %s are: %s" %
            (request.command, system.name, command_names))

    async def get_and_validate_parameters(
            self,
            request,
            command=None,
            command_parameters=None,
            request_parameters=None
    ):
        """Validates all request parameters

        Note: It is significant that we build the parameters as a separate object and then assign
        it. This is significant because when you are setting a value to None, mongoengine
        interprets this as "mark the item for deletion" meaning that when you save that attribute,
        it will actually get deleted. Sounds weird right? Well at least you didn't have to
        troubleshoot it.

        :param request: The Request to validate
        :param command: The the Command for this request. Will attempt to discover if None.
        :param command_parameters:  The command parameters.
        :param request_parameters: The request parameters.
        :return: The updated Parameters, ready to be saved to the database
        """
        self.logger.debug("Updating and Validating Parameters")

        if command is None:
            self.logger.debug("No Command Provided.")
            command = self.get_and_validate_command_for_system(request)

        if command_parameters is None:
            command_parameters = command.parameters

        if request_parameters is None:
            request_parameters = request.parameters

        self._validate_no_extra_request_parameter_keys(request_parameters, command_parameters)

        parameters_to_save = {}
        for command_parameter in command_parameters:
            self._validate_required_parameter_is_included_in_request(request, command_parameter,
                                                                     request_parameters)
            extracted_value = self._extract_parameter_value_from_request(request, command_parameter,
                                                                         request_parameters,
                                                                         command)
            await self._validate_value_in_choices(request, extracted_value, command_parameter)
            self._validate_maximum(extracted_value, command_parameter)
            self._validate_minimum(extracted_value, command_parameter)
            self._validate_regex(extracted_value, command_parameter)
            parameters_to_save[command_parameter.key] = extracted_value

        self.logger.debug("Successfully Updated and Validated Parameters.")
        self.logger.debug("Parameters: %s", parameters_to_save)
        return parameters_to_save

    async def _validate_value_in_choices(self, request, value, command_parameter):
        """Validate that the value(s) are valid according to the choice constraints"""
        if (value is not None and
                not command_parameter.optional and
                command_parameter.choices and
                command_parameter.choices.strict):

            choices = command_parameter.choices

            def map_param_values(kv_pair_list):
                param_map = {}
                for param_name, param_ref in kv_pair_list:
                    if param_ref == 'instance_name':
                        param_map[param_name] = request.instance_name
                    else:
                        param_map[param_name] = request.parameters[param_ref]

                return param_map

            if choices.type == 'static':
                if isinstance(choices.value, list):
                    allowed_values = choices.value
                elif isinstance(choices.value, dict):
                    key = choices.details.get('key_reference')
                    if key is None:
                        raise ModelValidationError(
                            "Unable to validate choices for parameter '%s' - Choices"
                            " with a dictionary value must specify a key_reference" %
                            command_parameter.key)

                    if key == 'instance_name':
                        key_reference_value = request.instance_name
                    else:
                        # Mongoengine stores None keys as 'null', so use that instead of None
                        key_reference_value = request.parameters.get(key) or 'null'

                    allowed_values = choices.value.get(key_reference_value)
                    if allowed_values is None:
                        raise ModelValidationError(
                            "Unable to validate choices for parameter '%s' - Choices"
                            " dictionary doesn't contain an entry with key '%s'" %
                            (command_parameter.key, key_reference_value))
                else:
                    raise ModelValidationError(
                        "Unable to validate choices for parameter '%s' - Choices value"
                        " must be a list or dictionary " % command_parameter.key)
            elif choices.type == 'url':
                parsed_value = parse(choices.value, parse_as='url')
                query_params = map_param_values(parsed_value['args'])

                response_json = json.loads(
                    self._session.get(parsed_value['address'], params=query_params).text)
                allowed_values = [item['value'] for item in response_json]
            elif choices.type == 'command':

                if isinstance(choices.value, six.string_types):
                    parsed_value = parse(choices.value, parse_as='func')
                    request = Request(
                        command=parsed_value['name'],
                        system=request.system,
                        system_version=request.system_version,
                        instance_name=request.instance_name,
                        parameters=map_param_values(parsed_value['args']),
                    )
                elif isinstance(choices.value, dict):
                    parsed_value = parse(choices.value['command'], parse_as='func')
                    request = Request(
                        command=parsed_value['name'],
                        system=choices.value.get('system'),
                        system_version=choices.value.get('version'),
                        instance_name=choices.value.get('instance_name', 'default'),
                        parameters=map_param_values(parsed_value['args']),
                    )
                else:
                    raise ModelValidationError(
                        "Unable to validate choices for parameter '%s' - Choices value"
                        " must be a string or dictionary " % command_parameter.key)

                response = await create_request(request, wait=True)

                parsed_output = json.loads(response.output)
                if isinstance(parsed_output, list):
                    if len(parsed_output) < 1:
                        raise ModelValidationError(
                            "Unable to validate choices for parameter '%s' - Result "
                            "of choices query was empty list" % command_parameter.key)

                    if isinstance(parsed_output[0], dict):
                        allowed_values = [item['value'] for item in parsed_output]
                    else:
                        allowed_values = parsed_output
                else:
                    raise ModelValidationError(
                        "Unable to validate choices for parameter '%s' - Result of "
                        " choices query must be a list" % command_parameter.key)
            else:
                raise ModelValidationError(
                    "Unable to validate choices for parameter '%s' - No valid type "
                    "specified (valid types are %s)" %
                    (command_parameter.key, Choices.TYPES))

            if command_parameter.multi:
                for single_value in value:
                    if single_value not in allowed_values:
                        msg = ("Value '%s' is not a valid choice for parameter with key '%s'. "
                               "Valid choices are: %s" %
                               (single_value, command_parameter.key, allowed_values))
                        self.logger.error(msg)
                        raise ModelValidationError(msg)
            else:
                if value not in allowed_values:
                    msg = ("Value '%s' is not a valid choice for parameter with key '%s'. "
                           "Valid choices are: %s" %
                           (value, command_parameter.key, allowed_values))
                    self.logger.error(msg)
                    raise ModelValidationError(msg)

    def _validate_maximum(self, value, command_parameter):
        """Validate that the value(s) are below the specified maximum"""
        if value is not None and not command_parameter.optional:
            if command_parameter.maximum:
                if isinstance(value, collections.Sequence):
                    if len(value) > command_parameter.maximum:
                        error_msg = ("Length %s is greater than the maximum allowed length (%s) "
                                     "for parameter %s" %
                                     (len(value), command_parameter.maximum, command_parameter.key))
                        self.logger.error(error_msg)
                        raise ModelValidationError(error_msg)
                else:
                    if value > command_parameter.maximum:
                        error_msg = ("Value %s is greater than the maximum allowed value (%s) "
                                     "for parameter %s" %
                                     (value, command_parameter.maximum, command_parameter.key))
                        self.logger.error(error_msg)
                        raise ModelValidationError(error_msg)

    def _validate_minimum(self, value, command_parameter):
        """Validate that the value(s) are above the specified minimum"""
        if value is not None and not command_parameter.optional:
            if command_parameter.minimum:
                if isinstance(value, collections.Sequence):
                    if len(value) < command_parameter.minimum:
                        error_msg = ("Length %s is less than the minimum allowed length (%s) "
                                     "for parameter %s" %
                                     (len(value), command_parameter.minimum, command_parameter.key))
                        self.logger.error(error_msg)
                        raise ModelValidationError(error_msg)
                else:
                    if value < command_parameter.minimum:
                        error_msg = ("Value %s is less than the minimum allowed value (%s) "
                                     "for parameter %s" %
                                     (value, command_parameter.minimum, command_parameter.key))
                        self.logger.error(error_msg)
                        raise ModelValidationError(error_msg)

    def _validate_regex(self, value, command_parameter):
        """Validate that the value matches the regex"""
        if value is not None and not command_parameter.optional:
            if command_parameter.regex:
                if not re.match(command_parameter.regex, value):
                    error_msg = ("Value %s does not match regular expression %s" %
                                 (value, command_parameter.regex))
                    self.logger.error(error_msg)
                    raise ModelValidationError(error_msg)

    def _extract_parameter_value_from_request(self, request, command_parameter, request_parameters,
                                              command):
        """Extracts the expected value based on the parameter in the database,
        uses the default and validates the type of the request parameter"""
        request_value = request_parameters.get(command_parameter.key, command_parameter.default)

        if request_value is None and command_parameter.nullable:
            return None

        if command_parameter.multi:
            request_values = request_value
            if not isinstance(request_values, list):
                raise ModelValidationError("%s was specified as a list, "
                                           "but was not provided as such" %
                                           command_parameter.key)

            value_to_return = []
            for value in request_values:
                value_to_return.append(
                    self._validate_parameter_based_on_type(value, command_parameter, command,
                                                           request))
        else:
            value_to_return = self._validate_parameter_based_on_type(request_value,
                                                                     command_parameter, command,
                                                                     request)

        return value_to_return

    def _validate_required_parameter_is_included_in_request(self, request, command_parameter,
                                                            request_parameters):
        """If the parameter is required but was not provided in the request_parameters and does
        not have a default, then raise a ValidationError"""
        self.logger.debug("Validating that Required Parameters are included in the request.")
        if not command_parameter.optional:
            if (command_parameter.key not in request_parameters
                    and command_parameter.default is None):
                self.logger.error("Required key: %s not provided in request. Parameters are: %s" %
                                  (command_parameter.key, request.parameters))
                raise ModelValidationError(
                    "Required key: %s not provided in request. Parameters are: %s" % (
                        command_parameter.key, request.parameters))

    def _validate_no_extra_request_parameter_keys(self, request_parameters, command_parameters):
        """Validate that all the parameters passed in were valid keys. If there is a key specified
        that is not noted in the database, then a validation error is thrown"""
        self.logger.debug("Validating Keys")
        valid_keys = [cp.key for cp in command_parameters]
        self.logger.debug("Valid Keys are : %s" % valid_keys)
        for key in request_parameters:
            if key not in valid_keys:
                self.logger.error(
                    "Unknown Key: %s provided in the parameters. Valid Keys are: %s" %
                    (key, valid_keys))
                raise ModelValidationError(
                    "Unknown Key: %s provided in the parameters. Valid Keys are: %s" %
                    (key, valid_keys))

    def _validate_parameter_based_on_type(self, value, parameter, command, request):
        """Validates the value passed in, ensures the type matches.
        Recursive calls for dictionaries which also have nested parameters"""

        try:
            if value is None and not parameter.nullable:
                raise ModelValidationError("There is no value for parameter '%s' "
                                           "and this field is not nullable." %
                                           parameter.key)
            elif parameter.type.upper() == "STRING":
                if isinstance(value, six.string_types):
                    return str(value)
                else:
                    raise TypeError("Invalid value for string (%s)" % value)
            elif parameter.type.upper() == "INTEGER":
                if int(value) != float(value):
                    raise TypeError("Invalid value for integer (%s)" % value)
                return int(value)
            elif parameter.type.upper() == "FLOAT":
                return float(value)
            elif parameter.type.upper() == "ANY":
                return value
            elif parameter.type.upper() == "BOOLEAN":
                if value in [True, False]:
                    return value
                else:
                    raise TypeError("Invalid value for boolean (%s)" % value)
            elif parameter.type.upper() == "DICTIONARY":
                dict_value = dict(value)
                if parameter.parameters:
                    self.logger.debug("Found Nested Parameters.")
                    return self.get_and_validate_parameters(request, command, parameter.parameters,
                                                            dict_value)
                return dict_value
            elif parameter.type.upper() == "DATE":
                return int(value)
            elif parameter.type.upper() == "DATETIME":
                return int(value)
            else:
                raise ModelValidationError(
                    "Unknown type for parameter. Please contact a system administrator.")
        except TypeError as ex:
            self.logger.exception(ex)
            raise ModelValidationError(
                "Value for key: %s is not the correct type. Should be: %s" %
                (parameter.key, parameter.type))
        except ValueError as ex:
            self.logger.exception(ex)
            raise ModelValidationError(
                "Value for key: %s is not the correct type. Should be: %s" %
                (parameter.key, parameter.type))
