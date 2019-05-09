import json
import logging

import mongoengine.errors

import brew_view
from bg_utils.mongo.models import Command
from bg_utils.mongo.parser import MongoParser
from brew_view.authorization import authenticated, Permissions
from brew_view.base_handler import BaseHandler


class NamespaceAPI(BaseHandler):

    parser = MongoParser()
    logger = logging.getLogger(__name__)

    @authenticated(permissions=[Permissions.COMMAND_READ])
    def get(self):
        """
        ---
        summary: Retrieve all Commands
        responses:
          200:
            description: All Commands
            schema:
              type: array
              items:
                $ref: '#/definitions/Command'
          50x:
            $ref: '#/definitions/50xError'
        tags:
          - Beta
        """
        self.logger.debug("Getting Namespaces")

        self.set_header("Content-Type", "application/json; charset=UTF-8")
        self.write(json.dumps(brew_view.config.namespaces))
        # try:
        #     self.write(
        #         self.parser.serialize_command(
        #             Command.objects.all(), many=True, to_string=True
        #         )
        #     )
        # except mongoengine.errors.DoesNotExist as ex:
        #     self.logger.error(
        #         "Got an error while attempting to serialize commands. "
        #         "This error usually indicates "
        #         "there are orphans in the database."
        #     )
        #     raise mongoengine.errors.InvalidDocumentError(ex)
