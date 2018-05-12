# A simplified DNS server with cache.

# import libs
import sys
import socket
import struct
import threading
import queue

import lib_Parsers
from lib_Parsers import RequestParser
from lib_Parsers import AnswerParser

MAX_SIZE=4096
AnswerQueue=queue.Queue()

class SendRequest(threading.Thread):
  def __init__(self,post,servaddr,cliaddr):
    threading.Thread.__init__(self)
    self.Sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    self.PostContext=post
    self.Servaddress=servaddr
    self.Clientaddrss=cliaddr
  def run(self):
    self.Sock.sendto(self.PostContext,self.Servaddress)
    AnswerQueue.put((self.Sock.recv(MAX_SIZE),self.Clientaddrss))

class SendAnswer(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.Sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
  def run(self):
    while True:
      if AnswerQueue.empty() == False:
        Post,Cliaddr=AnswerQueue.get()
        self.Sock.sendto(Post,Cliaddr)
        print('Sent answer to ',Cliaddr)


class DNS_Server:
  def __init__(self,mode='UDP',server="8.8.8.8",port=9290):
    self.mode=mode
    if mode=='UDP':
      self.Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    elif mode=='TCP':
      self.Socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    else:
      print('Error : Invalid protocol.\nPlease check your params.')
      sys.exit(1)
    self.Socket.bind(('127.0.0.1',port))
    self.serverIP=server
  def start(self):
    Server_address=(self.serverIP,53)
    if self.mode=='UDP':
      Answer_thread=SendAnswer()
      Answer_thread.start()
      while True:
        Post,Cliaddr=self.Socket.recvfrom(MAX_SIZE)
        print('Get DNS request from ',Cliaddr)
        Request_thread=SendRequest(Post,Server_address,Cliaddr)
        Request_thread.start()
        



if __name__ == "__main__":
  server=DNS_Server('UDP')
  server.start()
  