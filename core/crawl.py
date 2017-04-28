#!/usr/bin/env python3.4

"""A simple web crawler -- main driver program."""

# TODO:
# - Add arguments to specify TLS settings (e.g. cert/key files).

import argparse
import asyncio
# import logging
import sys

import crawling
import logs
import reporting
import utils


# from betacat.utils_funtion import argparse_parent_base


def start():
    """Main program.

    Parse arguments, set up event loop, run crawler, print report.
    """
    print('*****Starting crawling*******')

    parser = argparse.ArgumentParser(parents=[utils.get_parser()])
    args = parser.parse_args()
    if not args.roots:
        print('Use --help for command line help')
        return

    # setup log
    logs.setup_logging()

    if args.iocp:
        from asyncio.windows_events import ProactorEventLoop
        loop = ProactorEventLoop()
        asyncio.set_event_loop(loop)
    elif args.select:
        loop = asyncio.SelectorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        loop = asyncio.get_event_loop()

    roots = {utils.fix_url(root) for root in args.roots}

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
