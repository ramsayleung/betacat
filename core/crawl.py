#!/usr/bin/env python3.4

"""A simple web crawler -- main driver program."""

# TODO:
# - Add arguments to specify TLS settings (e.g. cert/key files).

import argparse
import asyncio
import logging
import sys

import crawling
import reporting
# from betacat.utils_funtion import argparse_parent_base


def fix_url(url):
    """Prefix a schema-less URL with http://."""
    if '://' not in url:
        url = 'http://' + url
    return url


def start():
    """Main program.

    Parse arguments, set up event loop, run crawler, print report.
    """
    # parser = argparse.ArgumentParser(parents=[argparse_parent_base.parser])

    parser = argparse.ArgumentParser(description="Web crawler")
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
    args = parser.parse_args()
    if not args.roots:
        print('Use --help for command line help')
        return

    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    logging.basicConfig(level=levels[min(args.level, len(levels) - 1)])

    if args.iocp:
        from asyncio.windows_events import ProactorEventLoop
        loop = ProactorEventLoop()
        asyncio.set_event_loop(loop)
    elif args.select:
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    roots = {fix_url(root) for root in args.roots}

    crawler = crawling.Crawler(roots,
                               exclude=args.exclude,
                               strict=args.strict,
                               max_redirect=args.max_redirect,
                               max_tries=args.max_tries,
                               max_tasks=args.max_tasks,
                               )
    try:
        loop.run_until_complete(crawler.crawl())  # Crawler gonna crawl.
    except KeyboardInterrupt:
        sys.stderr.flush()
        print('\nInterrupted\n')
    finally:
        reporting.report(crawler)
        crawler.close()

        # next two lines are required for actual aiohttp resource cleanup
        loop.stop()
        loop.run_forever()

        loop.close()


if __name__ == "__main__":
    start()
