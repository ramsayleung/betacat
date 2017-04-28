#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# author:Samray <samrayleung@gmail.com>
from collections import namedtuple

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

USERAGENT_PC = [
    "Mozilla/5.0 (Windows NT 5.1) Gecko/20100101 Firefox/14.0 Opera/12.0",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; de) Opera 11.51",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/2.1.7.6 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36",
]
USERAGENT_PHONE = [
    "Dalvik/2.1.0 (Linux; U; Android 5.0; Lenovo K50-t5 Build/LRX21M)",
    "Dalvik/2.1.0 (Linux; U; Android 5.1; m2 note Build/LMY47D)",
    "Mozilla/5.0 (iPad; CPU OS 4_3_5 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Mobile/9B176",
    "Mozilla/5.0 (iPad; CPU OS 5_0_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) FlyFlow/2.0 Mobile/9A405",
]
USERAGENT_ALL = USERAGENT_PC + USERAGENT_PHONE
