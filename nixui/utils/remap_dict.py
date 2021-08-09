def key_remapper(dictionary: dict, remap_dictionary: dict):
    return {remap_dictionary.get(k, k): v for k, v in dictionary.items()}
