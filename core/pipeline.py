#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# author:Samray <samrayleung@gmail.com>
from pymongo import MongoClient

from utils import get_mongodb_config  #


class MongodbHandler():
    def __init__(self):
        mongodb_config = get_mongodb_config()
        host = mongodb_config.get('host')
        port = mongodb_config.get('port')
        self.client = MongoClient(host, port)
