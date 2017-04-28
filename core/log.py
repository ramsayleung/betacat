#!/usr/bin/env python3
# # -*- coding: utf-8 -*-
# author:Samray <samrayleung@gmail.com>

import logging
import logging.handlers
import pickle
import socketserver
import struct


class LogRecordStreamHandler(socketserver.StreamRequestHandler):
    """Handler for a streaming logging request.

    This basically logs the record using whatever logging policy is
    configured locally.
    """

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handleLogRecord(record)

    def unPickle(self, data):
        return pickle.loads(data)

    def handleLogRecord(self, record):
        # if a name is specified, we use the named logger rather than the one
        # implied by the record.
        if self.server.logname is not None:
            name = self.server.logname
        else:
            name = record.name
        logger = logging.getLogger(name)
        # N.B. EVERY record gets logged. This is because Logger.handle
        # is normally called AFTER logger-level filtering. If you want
        # to do filtering, do it at the client end to save wasting
        # cycles and network bandwidth!
        logger.handle(record)


class LogRecordSocketReceiver(socketserver.ThreadingTCPServer):
    """
    Simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = True

    def __init__(self, host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT,
                 handler=LogRecordStreamHandler):
        socketserver.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort


class BetaCatLog(object):
    def __init__(self, name='betacat', default_log_level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(default_log_level)
        self.formatter = logging.Formatter(
            '%(levelname)s: %(asctime)s - %(module)s.%(funcName)s.%(lineno)d - %(message)s')

    def add_stream_handler(self, log_level=logging.DEBUG):
        handler = logging.StreamHandler
        handler.setFormatter(self.formatter)
        handler.setLevel(log_level)
        self.logger.addHandler(handler)

    def add_file_handler(self, filename, log_level=logging.INFO):
        handler = logging.FileHandler(filename)
        handler.setFormatter(self.formatter)
        handler.setLevel(log_level)
        self.logger.addHandler(handler)

    def add_remote_handler(self, server, level=logging.INFO):
        port = server.get("port", logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        host = server.get("host", "localhost")
        handler = logging.handlers.SocketHandler(host, port)
        handler.setLevel(level)
        self.logger.addHandler(handler)

    def get_logger(self):
        return self.logger


class BetaCatLogFactory(object):

    def __init__(self, filename=None, server=None, log_level=logging.DEBUG):
        self.filename = filename
        self.server = server
        self.log_level = log_level

    def get_logger(self):
        betacatLog = BetaCatLog(self.log_level)
        # default handler is stream handler
        betacatLog.set_stream_handler(self.log_level)

        if self.filename:
            betacatLog.add_file_handler(self.filename)

        if self.server:
            betacatLog.add_remote_handler(self.server)
