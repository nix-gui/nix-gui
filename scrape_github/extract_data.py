from nixui.utils import cache
from nixui.options import parser, nix_eval

import base64
import json
import os
import requests
import tempfile
import re


from github import Github


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


@cache.cache()
def blob_to_filebytes(token, blob_url):
    res = json.loads(requests.get(
        blob_url,
        headers={'Authorization': f'token {token}'}
    ).text)
    if 'tree' in res:
        print('found a directory ending in .nix, not processing this directory')
        return None
    if res.get('message') == 'Not Found':
        return None
    assert 'encoding' in res and res['encoding'] == 'base64', res
    return base64.b64decode(res['content'])


@cache.cache()
def get_option_values_for_all_configuration_nix(access_token, repo):
    with tempfile.TemporaryDirectory() as temp_dir:

        # write all nix files
        configuration_dot_nix_paths = set()
        blob_path_url_map = get_repos_blob_urls(access_token, repo)

        # repo too large, skipping
        if len(blob_path_url_map) > 500:
            return None

        for blob_path, blob_url in blob_path_url_map.items():
            file_path = os.path.join(temp_dir, blob_path)
            if file_path.endswith('/configuration.nix'):
                configuration_dot_nix_paths.add(file_path)
            if not os.path.exists(os.path.dirname(file_path)):
                os.makedirs(os.path.dirname(file_path))
            filebytes = blob_to_filebytes(access_token, blob_url)
            if filebytes is not None:
                with open(file_path, 'wb') as f:
                    f.write(filebytes)

        for path in configuration_dot_nix_paths:
            print('\t', path)
            try:
                return parser.get_all_option_values(path)
            except nix_eval.NixEvalError as e:
                if re.match("error: attribute '.*' missing", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: anonymous function at .* called without required argument '.*'", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: undefined variable '.*'", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: attempt to call something which is not a function but a", e.msg):
                    return None  # TODO: Handle
                elif re.findall(".* has an unfree license", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: file '.*' was not found in the Nix search path", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: attribute '.*' already defined at", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: syntax error", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: cannot read.*is not valid", e.msg):
                    return None  # TODO: Handle
                elif re.match("trace: Warning.*is deprecated and will be removed in the next release.", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: anonymous function at.*called with unexpected argument", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: cannot coerce a", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: string.*doesn't represent an absolute path", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: hash mismatch", e.msg):
                    return None  # TODO: Handle
                elif re.match("error: cannot import.*since path.*is not valid", e.msg):
                    return None  # TODO: Handle Maybe?
                elif re.match("error: deprecated", e.msg):
                    return None  # TODO: Handle Maybe?
                elif re.match("error: the contents of the file.*cannot be represented as a Nix string", e.msg):
                    return None  # TODO: Handle Maybe?
                elif re.match("error: getting status of '.*': Permission denied", e.msg):
                    return None  # ignore - file missing, requests root
                elif re.findall("error: opening file", e.msg):
                    return None  # ignore - file missing, repo may be valid but isn't usable for scraping
                elif re.findall("error: opening directory", e.msg):
                    return None  # ignore - file missing, repo may be valid but isn't usable for scraping
                elif re.match("error: getting status of", e.msg):
                    return None  # ignore - file missing, repo may be valid but isn't usable for scraping
                elif re.match("error: path '.*' has a trailing slash\n", e.msg):
                    return None  # ignore - weird git repo with # in filename https://github.com/bennofs/repros/tree/master/nixpkgs/%2319054
                elif re.match("error: fontconfig-ultimate has been removed", e.msg):
                    return None  # TODO: generic handler for specific messages like this?
                elif re.match("error: fetchurl does not support md5 anymore", e.msg):
                    return None  # TODO: generic handler for specific messages like this?
                elif re.match("error: sambaMaster was removed in", e.msg):
                    return None  # TODO: generic handler for specific messages like this?
                elif re.match("error:.*is not supported on.*refusing to evaluate", e.msg):
                    return None  # TODO: generic handler for specific messages like this?
                elif re.match("error: gnome.optionalPackages is removed since", e.msg):
                    return None  # TODO: generic handler for specific messages like this?
                else:
                    import pdb;pdb.set_trace()
                    print()
            except json.decoder.JSONDecodeError as e:
                return None  # TODO: Handle, file not valid linux path, e.g. `<nix-ld/modules/nix-ld.nix>`


def iter_repo_option_values(repos, access_token):
    count = 0
    for i, repo in enumerate(repos):
        print(repo)
        if repo in (
                'Alddar/new_infra',
                'Gtoyos/nixsys',
                'HendrikRoth/nixos-configuration__old',
                'Roxxers/nixconf',
                'ghuntley/ghuntley',
                'hurricanehrndz/dotfiles',
                'luka5/nixconfig',
                'noib3/dotfiles',
                'pniedzwiedzinski/raspberry',
        ):
            continue  # TODO: fix - idk why these repos configuration.nix have such weird parsing behavior
        option_values = get_option_values_for_all_configuration_nix(access_token, repo)
        if option_values:
            count += 1
            yield option_values
        else:
            print(repo, 'no options')
    print(count, '/', len(repos), 'found')
