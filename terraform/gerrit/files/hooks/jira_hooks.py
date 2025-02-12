#!/usr/bin/env python3

'''When a gerrit change is created or updated, update referenced Jira ticket'''

import argparse
import json
import logging
import os
import re
from pathlib import Path
from atlassian import Jira

# Custom Field identifier on https://couchbasecloud.atlassian.net/
GERRIT_CUSTOM_FIELD = 'customfield_11243'

def init_jira():
    '''Initialize jira session'''
    creds_file = str(Path.home()) + '/.ssh/jira-creds.json'
    jira_creds = json.loads(open(creds_file).read())
    jira = Jira(
        url=jira_creds['url'],
        username=jira_creds['username'],
        password=jira_creds['apitoken'],
        cloud=True)
    return jira

def get_tickets(commit_summary):
    '''Returns list of ticket IDs named by commit'''
    ticket_re = re.compile(r'(\b[A-Z][A-Z0-9]+-\d+\b)')
    return ticket_re.findall(commit_summary)

def patchset_created_jira(
        jira,
        issue_key,
        commit_summary,
        change_url,
        project_name,
        branch_name):
    '''
       Add gerrit info to Jira ticket if the ticket exist.
       If the gerrit review has already been added, skip.
    '''
    try:
        field_values = jira.issue(issue_key)
    except BaseException:
        logger.info(f'{issue_key} does not exist.')
        return
    review_list = []
    new_review_list = []
    commit_title = ' '.join(commit_summary.split(' ', 5)[:5])
    new_gerrit_entry = f'[{commit_title}|{change_url}]\trepo:{project_name}\tbranch:{branch_name}'
    gerrit_reviews = field_values['fields'][GERRIT_CUSTOM_FIELD]
    if gerrit_reviews:
        review_list = gerrit_reviews.split('\\\\')
        if new_gerrit_entry in review_list:
            return
        else:
            new_review_list = [e for e in review_list if not change_url in e]
    new_review_list.append(new_gerrit_entry)
    gerrit_reviews = '\\\\'.join(new_review_list)
    fields = {f'{GERRIT_CUSTOM_FIELD}': f'{gerrit_reviews}'}
    logger.info(f'Adding {commit_title} to {issue_key}')
    jira.update_issue_field(issue_key, fields)

def change_merged_jira(
        jira,
        issue_key,
        commit_summary,
        change_url,
        project_name,
        branch_name):
    '''Mark merged gerrit review by setting a checkbox next to it in the jira ticket.'''
    try:
        field_values = jira.issue(issue_key)
    except BaseException:
        logger.info(f'{issue_key} does not exist.')
        return
    review_list = []
    commit_title = ' '.join(commit_summary.split(' ', 5)[:5])
    gerrit_reviews = field_values['fields'][GERRIT_CUSTOM_FIELD]
    new_gerrit_entry = f'(/) [{commit_title}|{change_url}]\trepo:{project_name}\tbranch:{branch_name}'
    if gerrit_reviews:
        review_list = gerrit_reviews.split('\\\\')
    # In case gerrit summary is changed, filter out the review from existing list.
    # Add a new entry using the most updated gerrit summary
    new_review_list = [e for e in review_list if not change_url in e]
    new_review_list.append(new_gerrit_entry)
    gerrit_reviews = '\\\\'.join(new_review_list)
    fields = {f'{GERRIT_CUSTOM_FIELD}': f'{gerrit_reviews}'}
    logger.info(f'Mark {commit_title} as merged on {issue_key}')
    jira.update_issue_field(issue_key, fields)

# Main
parser = argparse.ArgumentParser()
parser.add_argument(
    '-e',
    '--event_type',
    help='Gerrit Event Type',
    required=True)
parser.add_argument(
    '-c',
    '--commit_summary',
    help='GIT Commit Summary',
    required=True)
parser.add_argument(
    '-u',
    '--change_url',
    help='GIT Change URL',
    required=True)
parser.add_argument(
    '-b',
    '--branch_name',
    help='GIT Branch',
    required=True)
parser.add_argument(
    '-p',
    '--project_name',
    help='GIT Repository',
    required=True)

args = parser.parse_args()

gerrit_site_path = os.getenv('GERRIT_SITE')
logger = logging.getLogger('jira_hook')
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler(
    f'{gerrit_site_path}/logs/{args.event_type}.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

tickets = get_tickets(args.commit_summary)

if tickets is not None:
    jira = init_jira()
    if args.event_type == 'patchset-created':
        for ticket in tickets:
            patchset_created_jira(
                jira,
                ticket,
                args.commit_summary,
                args.change_url,
                args.project_name,
                args.branch_name)
    if args.event_type == 'change-merged':
        for ticket in tickets:
            change_merged_jira(
                jira,
                ticket,
                args.commit_summary,
                args.change_url,
                args.project_name,
                args.branch_name)
else:
    logger.info('No ticket info on the commit summary')
