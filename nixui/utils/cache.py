import copy
import os
import hashlib


def cache(retain_hash_fn=(lambda: 0), return_copy=False):
    """
    retain_hash_fn: A function which gets a hash value from the passed args.
                    If the hash is the same as last run, use the hashed version.
    return_copy:    If true, return a copy of the hashed version
    """
    def cache(function):
        hash_memo = {}
        memo = {}
        def wrapper(*args, **kwargs):
            passed = (args, tuple(kwargs.items()))
            hashed_result = retain_hash_fn(*args, **kwargs)
            if passed in memo and hashed_result == hash_memo[passed]:
                res = memo[passed]
                if return_copy:
                    res = copy.deepcopy(res)
            else:
                res = function(*args, **kwargs)
                hash_memo[passed] = hashed_result
                memo[passed] = res
            return res
        return wrapper
    return cache


configuration_path_hash_fn = lambda: hashlib.sha256(open(os.environ['CONFIGURATION_PATH'], 'rb').read()).hexdigest()


lru_cache_file_unchanged = cache(lambda path: os.stat(path)[8])
