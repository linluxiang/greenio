#!/usr/bin/pypy
from server.simple_server import SimpleServer
from protocol.packet import PacketHandler

SimpleServer('localhost',7777,PacketHandler).glet.switch()
