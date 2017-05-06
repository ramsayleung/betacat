#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# author:Samray <samrayleung@gmail.com>
import cgi
import json
import logging
import re
import urllib.parse
from collections import namedtuple
from urllib.parse import urljoin

from lxml import html

LOGGER = logging.getLogger(__name__)


def lenient_host(host):
    parts = host.split('.')[-2:]
    return ''.join(parts)


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


class Parser():
    def __init__(self, roots, exclude=None, strict=True):
        self.exclude = exclude
        self.roots = roots
        self.strict = strict
        self.root_domains = set()
        for root in roots:
            parts = urllib.parse.urlparse(root)
            host, port = urllib.parse.splitport(parts.netloc)
            if not host:
                continue
            if re.match(r'\A[\d\.]*\Z', host):
                self.root_domains.add(host)
            else:
                host = host.lower()
                if self.strict:
                    self.root_domains.add(host)
                else:
                    self.root_domains.add(lenient_host(host))

    async def parse_links(self, response):
        """Return a FetchStatistic and list of links."""
        links = set()
        content_type = None
        encoding = None
        body = await response.read()
        jiayuan_search_url = 'http://search.jiayuan.com'
        if response.status == 200:
            content_type = response.headers.get('content-type')
            pdict = {}

            if content_type:
                content_type, pdict = cgi.parse_header(content_type)

            encoding = pdict.get('charset', 'utf-8')
            if content_type in ('text/html', 'application/xml'):
                text = await response.text()
                if jiayuan_search_url in response.url:
                    text.replace('##jiayser##', '')
                    text.replace(r'##jiayser##\\', '')
                    urls = await self.parse_search_result(text)
                if len(urls) != 0:
                    links = set(urls)
                else:
                    await self.parse_profile_detail(response)
                    # Replace href with (?:href|src) to follow image links.
                # urls = set(re.findall(r'''(?i)href=["']([^\s"'<>]+)''',
                #                       text))
                if urls:
                    LOGGER.debug('got %r distinct urls from %r',
                                 len(urls), response.url)
                for url in urls:
                    LOGGER.debug("response.url:%s,type:%s",
                                 response.url, type(response.url))
                    LOGGER.debug("parse_links url:%s,type:%s",
                                 url, type(url))
                    # normalized = urllib.parse.urljoin(str(response.url), url)
                    # defragmented, frag = urllib.parse.urldefrag(normalized)
                    # if self.url_allowed(defragmented):
                    #     links.add(defragmented)

        stat = FetchStatistic(
            url=response.url,
            next_url=None,
            status=response.status,
            exception=None,
            size=len(body),
            content_type=content_type,
            encoding=encoding,
            num_urls=len(links),
            # num_new_urls=len(links) - len(self.seen_urls))
            num_new_urls=3)

        return stat, links

    def url_allowed(self, url):
        if self.exclude and re.search(self.exclude, url):
            return False
        parts = urllib.parse.urlparse(url)
        if parts.scheme not in ('http', 'https'):
            LOGGER.debug('skipping non-http scheme in %r', url)
            return False
        host, port = urllib.parse.splitport(parts.netloc)
        if not self.host_okay(host):
            LOGGER.debug('skipping non-root host in %r', url)
            return False
        return True

    def host_okay(self, host):
        """Check if a host should be crawled.

        A literal match (after lowercasing) is always good.  For hosts
        that don't look like IP addresses, some approximate matches
        are okay depending on the strict flag.
        """
        host = host.lower()
        if host in self.root_domains:
            return True
        if re.match(r'\A[\d\.]*\Z', host):
            return False
        if self.strict:
            return self._host_okay_strictish(host)
        else:
            return self._host_okay_lenient(host)

    def _host_okay_strictish(self, host):
        """Check if a host should be crawled, strict-ish version.

        This checks for equality modulo an initial 'www.' component.
        """
        host = host[4:] if host.startswith('www.') else 'www.' + host
        return host in self.root_domains

    def _host_okay_lenient(self, host):
        """Check if a host should be crawled, lenient version.

        This compares the last two components of the host.
        """
        return lenient_host(host) in self.root_domains

    async def parge_profile_detail(self, response):
        text = await response.text()
        result = html.fromstring(text)

        # id('normal_user_container')/li/div/div[1]/a[2]/@href
        # //div[@class="bg_white mt15"]
        # id('smallImg')/div/ul/li/a/img
    async def parse_search_result(self, json_response):
        user_info = []
        user_id = []
        user_profile_url = []
        if json_response:
            result = await json.loads(json_response)
            user_info = result.get('userInfo')
            user_id = [info.get("realUid") for info in user_info]
            user_profile_url = [urljoin('http://www.jiayuan.com', id)
                                for id in user_id]  #
        return user_profile_url
