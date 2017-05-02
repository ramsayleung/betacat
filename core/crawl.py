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
    # if not args.roots:
    #     print('Use --help for command line help')
    #     return

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

    roots = []
    female_url = 'http://search.jiayuan.com/v2/index.php?key=&sex=f&stc=&sn=default&sv={}&p=1&pt=60843&ft=off&f=select&mt=d'
    female_url_page_total = 60843
    male_url = 'http://search.jiayuan.com/v2/index.php?key=&sex=m&stc=&sn=default&sv=1&p={}&pt=84769&ft=off&f=select&mt=d'
    male_url_page_total = 84763
    for i in range(1, female_url_page_total + 1):
        roots.append(female_url.format(i))
    for i in range(1, male_url_page_total + 1):
        roots.append(male_url.format(i))
    # roots = {utils.fix_url(root) for root in args.roots}

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
