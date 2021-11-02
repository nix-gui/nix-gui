import copy
import functools
import json
import os
import hashlib
import pickle

import nixui
from nixui.utils import store


@functools.lru_cache()
def _get_cache_path(call_signature, key):
    module, function, args, kwargs = call_signature
    hashval = hashlib.md5(json.dumps([args, kwargs], sort_keys=True).encode('utf-8')).hexdigest()
    filename = f'{_get_version()}/{module}/{function}/{hashval}.{key}'
    path = os.path.join(
        store.get_store_path(),
        'func_cache',
        filename
    )
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    return path


def _save_to_disk_cache(call_signature, key, return_value):
    filepath = _get_cache_path(call_signature, key)
    with open(filepath, 'wb') as f:
        pickle.dump(return_value, f)


def _get_from_disk_cache(call_signature, key):
    filepath = _get_cache_path(call_signature, key)
    with open(filepath, 'rb') as f:
        return pickle.load(f)


def _get_version():
    return nixui.__version__


def _is_in_disk_cache(call_signature, key):
    return os.path.exists(_get_cache_path(call_signature, key))


@functools.lru_cache()
def _use_diskcache():
    return json.loads(os.environ.get('USE_DISKCACHE', 'true'))


def cache(retain_hash_fn=(lambda *args, **kwargs: 0), return_copy=True, diskcache=True):
    """
    retain_hash_fn: A function which gets a hash value from the passed args.
                    If the hash is the same as last run, use the cached version.
    return_copy:    If true, return a copy of the cached version
    diskcache:      Persist the function results to disk for repeat runs
    """
    def cache(function):
        args_hash_result_map = {}
        args_return_value_map = {}
        def wrapper(*args, **kwargs):
            hash_result = retain_hash_fn(*args, **kwargs)
            call_signature = (function.__module__, function.__name__, args, tuple(kwargs.items()))

            if diskcache and _use_diskcache():
                # if fn-arg results cached in disk but not in memory, load disk to memory
                if call_signature not in args_return_value_map:
                    if _is_in_disk_cache(call_signature, 'result'):
                        try:
                            hash_result = _get_from_disk_cache(call_signature, 'hash_result')
                            result = _get_from_disk_cache(call_signature, 'result')
                        except EOFError:
                            pass  # indicates that the cached result didn't save properly
                        else:
                            args_hash_result_map[call_signature] = hash_result
                            args_return_value_map[call_signature] = result

            # if cached in memory and the hash-check is consistent, return the memcached result, otherwise calculate the result
            if call_signature in args_return_value_map and hash_result == args_hash_result_map[call_signature]:
                res = args_return_value_map[call_signature]
                if return_copy:
                    res = copy.copy(res)
            else:
                res = function(*args, **kwargs)
                args_hash_result_map[call_signature] = hash_result
                args_return_value_map[call_signature] = res

            if diskcache and _use_diskcache() and not _is_in_disk_cache(call_signature, 'result'):
                _save_to_disk_cache(call_signature, 'result', res)
                _save_to_disk_cache(call_signature, 'hash_result', hash_result)

            return res
        return wrapper
    return cache


configuration_path_hash_fn = lambda: hashlib.sha256(open(os.environ['CONFIGURATION_PATH'], 'rb').read()).hexdigest()
first_arg_path_hash_fn = lambda path=None: hashlib.sha256(open(path or os.environ['CONFIGURATION_PATH'], 'rb').read()).hexdigest()
