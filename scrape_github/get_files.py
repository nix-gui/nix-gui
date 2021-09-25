import itertools
import time

from github import Github

from nixui.utils import cache


API_REQUEST_LIMIT_PERIOD = 60 * 60 / 1000


"""
RETRIEVAL
1) retrieve the set of repos containing nix configurations
- TODO: exclude forks
- base query is "filename:configuration.nix" or "filename:home.nix"
    (later on simply run "extension:nix" and parse all nix files when nix-gui is capable)
- github search api allows up to 1000 results, this query returns about 7,000 results
  - shard the results with all permutations of "-foo" and "foo" for `foo` in
    "timeZone", "console", "systemPackages", "networking", "services", "users", "fonts", "boot"
2) crawl each repo for nix files
3) download all nix files (for initial trial run, just download configuration.nix and hardware-configuration.nix
"""


@cache.cache()
def get_repos_for_query(access_token, query):
    time.sleep(1)
    print('running', query)
    g = Github(access_token)
    results = g.search_code(query)
    repo_names = set()

    print('found', results.totalCount, 'results for', query)
    if results.totalCount == 1000:
        raise Exception()
        print('WARNING: more than 1000 results for', query)

    elif results.totalCount == 0:
        return repo_names

    for i, result in enumerate(results):
        print(i)
        time.sleep(0.5)
        if 'nixpkgs' not in result.repository.full_name:
            repo_names.add(result.repository.full_name)


    return repo_names


def get_relevant_repos(access_token):
    """
    TODO: implement scraping for non configuration.nix files and parse all .nix files on github

    Query 0: `extension:nix filename:"configuration.nix"`
    Query 1: `extension:nix filename:"home.nix"`
    """
    search_params = ("timeZone", "systemPackages", "networking", "services", "fonts", "boot", "usb_storage", "ahci")
    base_queries = [
        'extension:nix filename:"configuration.nix"',
        'extension:nix filename:"home.nix"',
    ]
    repo_names = set()
    for base_query in base_queries:
        for search_flags in itertools.product([False, True], repeat=len(search_params)):
            query = base_query + " " + " ".join([
                ('' if flag else '-') + param
                for flag, param in zip(search_flags, search_params)
            ])
            repo_names |= get_repos_for_query(access_token, query)
    return repo_names


def retry_get_repos(access_token):
    for i in range(100):
        try:
            repos = get_relevant_repos(access_token)
        except Exception as e:
            print(e)
            time.sleep(100)
            continue
        break
    return repos
