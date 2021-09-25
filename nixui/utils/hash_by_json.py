import dataclasses
import json


# https://stackoverflow.com/questions/51286748/make-the-python-json-encoder-support-pythons-new-dataclasses/51286749#51286749
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


def hash_object(obj):
    json_string = json.dumps(
        obj,
        sort_keys=True,
        cls=EnhancedJSONEncoder,
    )
    return hash(json_string)
