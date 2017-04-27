#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# author:Samray <samrayleung@gmail.com>
import asyncio
import logging
import urllib
from asyncio import Queue
from collections import namedtuple

import aiohttp
import utils

LOGGER = logging.getLogger(__name__)

FetchStatistic = namedtuple('FetchStatistic',
                            ['url',
                             'next_url',
                             'status',
                             'exception',
                             'size',
                             'content_type',
                             'encoding',
                             'num_urls',
                             'num_new_urls'])


class Fetcher():
    def __init__(self, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.task_queue = Queue(loop=self.loop)
        self.session = aiohttp.ClientSession(loop=self.loop)

    def is_redirect(self, response):
        return response.status in (300, 301, 302, 303, 307)

    async def fetch(self, url, max_redirect=10, max_tries=4):
        """Fetch one URL."""
        tries = 0
        exception = None
        while tries < self.max_tries:
            try:
                response = await self.session.get(
                    url, allow_redirects=False)

                if tries > 1:
                    LOGGER.info('try %r for %r success', tries, url)

                break
            except aiohttp.ClientError as client_error:
                LOGGER.info('try %r for %r raised %r',
                            tries, url, client_error)
                exception = client_error

            tries += 1
        else:
            # We never broke out of the loop: all tries failed.
            LOGGER.error('%r failed after %r tries',
                         url, self.max_tries)
            self.record_statistic(FetchStatistic(url=url,
                                                 next_url=None,
                                                 status=None,
                                                 exception=exception,
                                                 size=0,
                                                 content_type=None,
                                                 encoding=None,
                                                 num_urls=0,
                                                 num_new_urls=0))
            return

        try:
            if self.is_redirect(response):
                location = response.headers['location']
                next_url = urllib.parse.urljoin(url, location)
                self.record_statistic(FetchStatistic(url=url,
                                                     next_url=next_url,
                                                     status=response.status,
                                                     exception=None,
                                                     size=0,
                                                     content_type=None,
                                                     encoding=None,
                                                     num_urls=0,
                                                     num_new_urls=0))

                if next_url in self.seen_urls:
                    return
                if max_redirect > 0:
                    LOGGER.info('redirect to %r from %r', next_url, url)
                    self.add_url(next_url, max_redirect - 1)
                else:
                    LOGGER.error('redirect limit reached for %r from %r',
                                 next_url, url)
            else:
                stat, links = await self.parse_links(response)
                self.record_statistic(stat)
                for link in utils.difference(links, self.seen_urls):

                    # for link in links.difference(self.seen_urls):
                    self.q.put_nowait((link, self.max_redirect))
                # self.seen_urls.update(links)
                self.seen_urls.update(links)
        finally:
            await response.release()
