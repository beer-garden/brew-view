from functools import partial

import brewtils.schemas
from bg_utils.mongo.parser import MongoParser
from brewtils.schema_parser import SchemaParser
from brewtils.test.comparable import assert_system_equal


def convert(model, parser=None):
    schema = getattr(brewtils.schemas, model.schema)
    return parser._do_parse(
        SchemaParser._do_serialize(schema(), model, True), schema(), True
    )


mongo2brew = partial(convert, parser=SchemaParser)
brew2mongo = partial(convert, parser=MongoParser)


def test_convert(bg_system):
    mongo = brew2mongo(bg_system)
    brew = mongo2brew(mongo)

    assert_system_equal(brew, bg_system)
