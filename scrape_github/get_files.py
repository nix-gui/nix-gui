import itertools
import time

from github import Github

from nixui.utils import cache


API_REQUEST_LIMIT_PERIOD = 60 * 60 / 1000


"""
RETRIEVAL
1) retrieve the set of repos containing nix configurations
- TODO: exclude forks
- base query is "filename:configuration.nix" (later on do "extension:nix" instead)
- github search api allows up to 1000 results, this query returns about 7,000 results
  - shard the results with all permutations of "-foo" and "foo" for `foo` in
    "timeZone", "console", "systemPackages", "networking", "services", "users", "fonts", "boot"
2) crawl each repo for nix files
3) download all nix files (for initial trial run, just download configuration.nix and hardware-configuration.nix
"""


@cache.cache()
def get_repos_for_query(access_token, query):
    print('running', query)
    g = Github(access_token)
    results = g.search_code(query)
    repo_names = set()

    print('found', results.totalCount, 'results for', query)
    if results.totalCount == 1000:
        print('WARNING: more than 1000 results for', query)

    elif results.totalCount == 0:
        return repo_names

    for result in results:
        repo_names.add(result.repository.full_name)
        time.sleep(1)

    return repo_names



def get_relevant_repos(access_token):
    base_query = "filename:configuration.nix extension:nix"
    search_params = ("timeZone", "console", "systemPackages", "networking", "services", "users", "fonts", "boot")
    repo_names = set()
    for search_flags in itertools.product([False, True], repeat=len(search_params)):
        query = base_query + " " + " ".join([
            ('' if flag else '-') + param
            for flag, param in zip(search_flags, search_params)
        ])
        repo_names |= get_repos_for_query(access_token, query)
    return repo_names
