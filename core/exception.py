#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# author:Samray <samrayleung@gmail.com>


class DependencyNotSatified(Exception):
    def __init__(self, dependency):
        self.dependency = dependency

    def __str__(self):
        return 'Dependency {} is not satisfied'.format(self.dependency)
