"""
DATA PROCESSING

Parse the files to retrieve the following data
- which options are most frequently set
- what type is each specific option most frequently set as
- association-matrix of option settings within a repo
"""
from scrape_github import get_files, extract_data

import json
import collections
import sys


def iter_repo_data():
    access_token = sys.argv[1]
    repos = sorted(get_files.retry_get_repos(access_token))
    for repo, option_data in zip(repos, extract_data.iter_repo_option_values(repos, access_token)):
        yield repo, option_data


def get_option_frequency_rank():
    count = collections.defaultdict(int)
    for i, (repo, option_data) in enumerate(iter_repo_data()):
        for attribute in option_data:
            count[str(attribute)] += 1
    return i + 1, count


def get_option_type_frequency():
    type_count = collections.defaultdict(lambda: collections.defaultdict(int))
    for i, (repo, option_data) in enumerate(iter_repo_data()):
        for attribute, definition in option_data.items():
            type_count[str(attribute)][definition.obj_type] += 1
    return type_count


def get_option_association_matrix():
    association_count = collections.defaultdict(lambda: collections.defaultdict(int))
    for i, (repo, option_data) in enumerate(iter_repo_data()):
        attributes_in_repo = set(option_data.keys())
        for attribute in attributes_in_repo:
            for assoc_attr in attributes_in_repo:
                association_count[str(attribute)][str(assoc_attr)] += 1

    association_probability = collections.defaultdict(lambda: collections.defaultdict(int))
    total_num_repos, attr_count = get_option_frequency_rank()
    for attr, count in attr_count.items():
        if count < 5:
            continue
        for associated_attr, assoc_count in association_count[attr].items():
            association_probability[attr][associated_attr] = assoc_count / count

    return association_probability


def main():
    association_matrix = get_option_association_matrix()
    type_frequency = get_option_type_frequency()
    num_repos, count = get_option_frequency_rank()

    json.dump(
        association_matrix,
        open('association_matrix.json', 'w')
    )
    json.dump(
        type_frequency,
        open('type_frequency.json', 'w')
    )
    json.dump(
        count,
        open('instance_count.json', 'w')
    )
