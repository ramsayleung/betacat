#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# author:Samray <samrayleung@gmail.com>

import asyncio
import logging

import aiohttp

from configuration import FetchStatistic

LOGGER = logging.getLogger(__name__)


class Fetcher():
    def __init__(self, session, max_tries=4):
        self.max_tries = max_tries
        self.session = session

    async def fetch(self, url, max_redirect, params, method='get'):
        """Fetch one URL."""
        tries = 0
        exception = None
        while tries < self.max_tries:
            try:
                if method == 'get':
                    if params:
                        response = await self.session.get(
                            url, allow_redirects=False, params=self.params)
                    else:
                        response = await self.session.get(
                            url, allow_redirects=False)
                else:
                    response = await self.session.post(url, data=params)

                if tries > 1:
                    LOGGER.debug('try %r for %r success', tries, url)

                return response, url, max_redirect, None
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
            FetchStatistic(url=url,
                           next_url=None,
                           status=None,
                           exception=exception,
                           size=0,
                           content_type=None,
                           encoding=None,
                           num_urls=0,
                           num_new_urls=0)
            return response, url, max_redirect, FetchStatistic
