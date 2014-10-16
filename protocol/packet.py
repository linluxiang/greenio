import asyncore_epoll as asyncore
import socket
from greenlet import greenlet

class PacketIO(asyncore.dispatcher):
    def __init__(self,socket,handler,scheduler):
        asyncore.dispatcher.__init__(self,socket)
        self.handler = handler
        self.scheduler= scheduler 
        self.error = 0
        self.should_read = False
        self.should_write= False
        self.input = None
        self.output = None
        self.nextlen = 0
        self.temp = ''

    def read(self):
        self.input = None
        self.error = 0
        self.should_read = True
        self.scheduler.switch()

    def readable(self):
        return self.should_read

    def genPacketHeader(size):
        return chr(size/(256**3)) + chr(size/(256**2)) + chr(size/(256)) + chr(size%256)
    
    def write(self,output):
        self.output = output
        self.error = 0
        self.should_write = True
        plen = len(self.output)
        self.temp = self.genPacketHeader()
        self.scheduler.switch()

    def writable(self):
        return self.should_write
    
    def doerror(self,error):
        print 'on error'
        self.close()
        self.error = error
        self.handler.switch()

    def handle_write(self):
        if len(self.temp) > 0:
            sent = self.send(self.temp)
            if sent >=0:
                self.temp=self.temp[sent:]
            else:
                doerror(2)
            return
        else:
            if len(self.output) > 0:
                sent = self.send(self.output)
                if sent>=0:
                    self.output = self.output[sent:]
                else:
                    doerror(2)
            else:
                self.output = None
                self.error=0
                self.handler.switch()
    
    def handle_read(self):
        if self.nextlen==0:
            data = self.recv(4-len(self.temp))
            if len(data) <  4-len(self.temp):
                self.temp += data
                return
            self.temp+= data
            self.nextlen = ord(self.temp[0])*(256**3) + ord(self.temp[1])*(256**2) + ord(self.temp[2]) *256 + ord(self.temp[3])
            print self.nextlen
            self.temp = ''
            if self.nextlen > 1024**2:
                print self.nextlen
                self.doerror(1)
        else:
            data = self.recv(self.nextlen-len(self.temp))
            if len(data) <  self.nextlen-len(self.temp):
                self.temp += data
                return
            self.temp+=data
            self.input = self.temp
            self.nextlen = 0
            self.temp = ''
            self.should_read= False
            self.handler.switch()

    def handle_close(self):
        self.should_read= False
        self.error = -1
        self.handler.switch()
        #handle close to release session related resources
        pass


class PacketHandler:
    def __init__(self,socket,scheduler):
        self.scheduler = scheduler
        self.glet = greenlet(self.routine)
        self.glet.parent = scheduler.glet
        self.packetio = PacketIO(socket,self.glet,scheduler.glet)

    def routine(self):
        self.packetio.read()
        if self.packetio.error==0:
            self.process()
        print 'greenlet finished'

    def process(self):
        print self.packetio.input
        pass
