#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# author:Samray <samrayleung@gmail.com>
import argparse
import os
import random

import yaml

from configuration import USERAGENT_ALL, USERAGENT_PC, USERAGENT_PHONE


def difference(links_set, seen_bloomfilter):
    unseen_links = []
    for link in links_set:
        if link not in seen_bloomfilter:
            unseen_links.append(link)
    return unseen_links


def get_parser():
    parser = argparse.ArgumentParser(description="Web crawler", add_help=False)
    parser.add_argument(
        '--iocp', action='store_true', dest='iocp',
        default=False, help='Use IOCP event loop (Windows only)')
    parser.add_argument(
        '--select', action='store_true', dest='select',
        default=False, help='Use Select event loop instead of default')
    parser.add_argument(
        'roots', nargs='*',
        default=[], help='Root URL (may be repeated)')
    parser.add_argument(
        '--max_redirect', action='store', type=int, metavar='N',
        default=10, help='Limit redirection chains (for 301, 302 etc.)')
    parser.add_argument(
        '--max_tries', action='store', type=int, metavar='N',
        default=4, help='Limit retries on network errors')
    parser.add_argument(
        '--max_tasks', action='store', type=int, metavar='N',
        default=100, help='Limit concurrent connections')
    parser.add_argument(
        '--exclude', action='store', metavar='REGEX',
        help='Exclude matching URLs')
    parser.add_argument(
        '--strict', action='store_true',
        default=True, help='Strict host matching (default)')
    parser.add_argument(
        '--lenient', action='store_false', dest='strict',
        default=False, help='Lenient host matching')
    parser.add_argument(
        '-v', '--verbose', action='count', dest='level',
        default=2, help='Verbose logging (repeat for more verbose)')
    parser.add_argument(
        '-q', '--quiet', action='store_const', const=0, dest='level',
        default=2, help='Only log errors')

    return parser


def fix_url(url):
    """Prefix a schema-less URL with http://."""
    if '://' not in url:
        url = 'http://' + url
    return url


def get_useragent(useragent_type='all'):
    """
    if not specified, get a random useragent.
    """
    useragent_type = useragent_type.lower()
    return random.choice(USERAGENT_ALL if useragent_type == 'all' else
                         (USERAGENT_PC if useragent_type == 'pc'
                          else USERAGENT_PHONE))


def get_mongodb_config():
    path = 'application.yaml'
    if os.path.exists(path):
        with open(path, 'rt') as f:
            application_configratio = yaml.safe_load(f.read())
        return application_configratio.get('mongodb')
    else:
        mongodb = {'host': 'localhost', 'port': 27017}
        return mongodb
