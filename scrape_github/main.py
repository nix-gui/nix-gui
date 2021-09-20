import base64
import json
import os
import requests
import sys
import tempfile
import time
import re


from github import Github

from scrape_github import get_files

from nixui.options import parser, nix_eval
from nixui.utils import cache


@cache.cache()
def get_repos_blob_urls(access_token, repo_name):
    g = Github(access_token)
    user, repo = repo_name.split('/')
    repo = g.get_user(user).get_repo(repo)

    return {
        tree_elem.path: tree_elem.url
        for tree_elem in repo.get_git_tree(repo.default_branch, True).tree
        if tree_elem.path[-4:] == '.nix'
    }


def retry_get_repos(access_token):
    for i in range(100):
        try:
            repos = get_files.get_relevant_repos(access_token)
        except Exception as e:
            print(e)
            time.sleep(100)
            continue
        break
    return repos


@cache.cache()
def blob_to_filebytes(token, blob_url):
    res = json.loads(requests.get(
        blob_url,
        headers={'Authorization': f'token {token}'}
    ).text)
    if 'tree' in res:
        #print('found a directory ending in .nix, not processing this directory')
        return None
    if res.get('message') == 'Not Found':
        return None
    assert 'encoding' in res and res['encoding'] == 'base64', res
    return base64.b64decode(res['content'])


def main():
    access_token = sys.argv[1]

    repos = retry_get_repos(access_token)

    res = {}
    for i, repo in enumerate(sorted(repos)):
        #print(repo)
        with tempfile.TemporaryDirectory() as temp_dir:

            # write all nix files
            configuration_dot_nix_paths = set()
            blob_path_url_map = get_repos_blob_urls(access_token, repo)
            if len(blob_path_url_map) > 500:
                #print(f'!!!!\tskipping, repo too large: {len(blob_path_url_map)} files')
                continue
            else:
                pass
                #print(f'\t\tprocessing {len(blob_path_url_map)} files')
            for blob_path, blob_url in blob_path_url_map.items():
                file_path = os.path.join(temp_dir, blob_path)
                if file_path.endswith('/configuration.nix'):
                    #print(file_path)
                    configuration_dot_nix_paths.add(file_path)
                if not os.path.exists(os.path.dirname(file_path)):
                    os.makedirs(os.path.dirname(file_path))
                filebytes = blob_to_filebytes(access_token, blob_url)
                if filebytes is not None:
                    with open(file_path, 'wb') as f:
                        f.write(filebytes)

            for path in configuration_dot_nix_paths:
                print(repo, path)
                try:
                    option_values = parser.get_all_option_values(path)
                except nix_eval.NixEvalError as e:
                    if re.match("error: attribute '.*' missing", e.msg):
                        continue  # TODO: Handle
                    elif re.match("error: anonymous function at .* called without required argument '.*'", e.msg):
                        continue  # TODO: Handle
                    elif re.match("error: undefined variable '.*'", e.msg):
                        continue  # TODO: Handle
                    elif re.match("error: attempt to call something which is not a function but a set", e.msg):
                        continue  # TODO: Handle
                    elif re.match("error: Package .* has an unfree license", e.msg):
                        continue  # TODO: Handle
                    elif re.match("error: getting status of '.*': Permission denied", e.msg):
                        continue  # ignore - file missing, requests root
                    elif re.match("error: opening file", e.msg):
                        continue  # ignore - file missing, repo may be valid but isn't usable for scraping
                    else:
                        import pdb;pdb.set_trace()
                        print()
                except json.decoder.JSONDecodeError as e:
                    continue


    """
    print(list(repos)[0])
    import cProfile
    import pstats
    import os
    with cProfile.Profile() as profile:
        option_values = parser.get_all_option_values('/home/andrew/p/nix-gui/nixui/tests/sample/configuration.nix')
        for attribute, definition in option_values.items():
            print(definition.expression_string, definition.obj)
        p = pstats.Stats(profile)
        p.strip_dirs()
        p.sort_stats('cumtime')
        p.print_stats(50)
    """
