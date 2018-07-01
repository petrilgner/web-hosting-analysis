import json
import pprint


def print_dict(g_dict):
    pprint.pprint(g_dict)


def print_dict_json(g_dict):
    print(json.dumps(g_dict, indent=1))
