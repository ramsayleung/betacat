#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# author:Samray <samrayleung@gmail.com>


def difference(links_set, seen_bloomfilter):
    unseen_links = []
    for link in links_set:
        if link in seen_bloomfilter:
            unseen_links.append(link)
    return unseen_links
