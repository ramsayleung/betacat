"""A simple web crawler -- class implementing crawling logic."""

import asyncio
import cgi
import logging
import re
import time
import urllib.parse
from asyncio import Queue
from collections import namedtuple

import aiohttp  # Install with "pip install aiohttp".
import utils
from fetcher import Fetcher
from parser import Parser
from pybloomfilter import BloomFilter

LOGGER = logging.getLogger(__name__)


def lenient_host(host):
    parts = host.split('.')[-2:]
    return ''.join(parts)


def is_redirect(response):
    return response.status in (300, 301, 302, 303, 307)


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


class Crawler:
    """Crawl a set of URLs.

    This manages two sets of URLs: 'urls' and 'done'.  'urls' is a set of
    URLs seen, and 'done' is a list of FetchStatistics.
    """

    def __init__(self, roots,
                 exclude=None, strict=True,  # What to crawl.
                 max_redirect=10, max_tries=4,  # Per-url limits.
                 max_tasks=10, *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.roots = roots
        self.exclude = exclude
        self.strict = strict
        self.max_redirect = max_redirect
        self.max_tries = max_tries
        self.max_tasks = max_tasks
        self.q = Queue(loop=self.loop)
        self.seen_urls = BloomFilter(10000000, 0.01)
        self.done = []
        self.session = aiohttp.ClientSession(loop=self.loop)
        for root in roots:
            self.add_url(root)
        self.t0 = time.time()
        self.parser = Parser(
            roots=self.roots, exclude=self.exclude, strict=self.strict)
        self.fetcher = Fetcher(loop=self.loop, max_tries=self.max_tries)
        self.t1 = None

    def close(self):
        """Close resources."""
        self.session.close()

    def record_statistic(self, fetch_statistic):
        """Record the FetchStatistic for completed / failed URL."""
        self.done.append(fetch_statistic)

    async def handle_response(self, response, url, max_redirect):
        try:
            if is_redirect(response):
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
                stat, links = await self.parser.parse_links(response)
                self.record_statistic(stat)
                for link in utils.difference(links, self.seen_urls):

                    # for link in links.difference(self.seen_urls):
                    self.q.put_nowait((link, self.max_redirect))
                # self.seen_urls.update(links)
                self.seen_urls.update(links)
        finally:
            await response.release()

    async def work(self):
        """Process queue items forever."""
        try:
            while True:
                url, max_redirect = await self.q.get()
                assert url in self.seen_urls
                LOGGER.info("url:%s", url)
                LOGGER.info("max_redirect:%s", max_redirect)
                response, url, max_redirect, FetchStat = await self.fetcher.fetch(url, max_redirect)
                if FetchStat:
                    self.record_statistic(FetchStat)
                if response:
                    await self.handle_response(response, url, max_redirect)
                self.q.task_done()
        except asyncio.CancelledError:
            pass

    def add_url(self, url, max_redirect=None):
        """Add a URL to the queue if not seen before."""
        if max_redirect is None:
            max_redirect = self.max_redirect
        LOGGER.debug('adding %r %r', url, max_redirect)
        self.seen_urls.add(url)
        self.q.put_nowait((url, max_redirect))

    async def crawl(self):
        """Run the crawler until all finished."""
        workers = [asyncio.Task(self.work(), loop=self.loop)
                   for _ in range(self.max_tasks)]
        self.t0 = time.time()
        await self.q.join()
        self.t1 = time.time()
        for w in workers:
            w.cancel()
