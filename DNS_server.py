# A simplified DNS server with cache.

# import libs
import sys
import socket
import struct
import threading
import queue
import redis

import lib_Parsers
from lib_Parsers import RequestParser
from lib_Parsers import AnswerParser

MAX_SIZE=4096
MAX_CLIENT=5
DATABASE_NAME='DNS_server_cache'
AnswerQueue=queue.Queue()

class SendRequest(threading.Thread):
  def __init__(self,post,servaddr,cliaddr):
    threading.Thread.__init__(self)
    self.cache=redis.Redis(host='127.0.0.1',port=6379,db=0)
    self.Sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    self.PostContext=post
    self.Servaddress=servaddr
    self.Clientaddress=cliaddr
  def run(self):
    url=RequestParser(self.PostContext)['url']
    QuestionNum=RequestParser(self.PostContext)['QuestionNum']
    cached=True
    for i in range(0,QuestionNum):
      if self.cache.hexists(DATABASE_NAME,url[i]) == 0:
        cached=False
    if cached == True:
      for i in range(0,QuestionNum):
        AnswerQueue.put((self.cache.hget(DATABASE_NAME,url[i]),self.Clientaddress))
    else:
      self.Sock.sendto(self.PostContext,self.Servaddress)
      for i in range(0,QuestionNum):
        Answer=self.Sock.recv(MAX_SIZE)
        self.cache.hset(DATABASE_NAME,url[i],Answer)
        AnswerQueue.put((Answer,self.Clientaddress))

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

class TCPconnect(threading.Thread):
  def __init__(self,servaddr,Clisock):
    threading.Thread.__init__(self)
    self.Serversock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    self.Clientsock=Clisock
    self.servaddr=servaddr
  def run(self):
    Post=self.Clientsock.recv(MAX_SIZE)
    self.Serversock.sendto(Post,self.servaddr)
    Post=self.Serversock.recv(MAX_SIZE)
    self.Clientsock.send(Post)
    self.Clientsock.close()
    print('Connection closed.')

class DNS_Server:
  def __init__(self,mode='UDP',server="8.8.8.8",port=9190):
    self.mode=mode
    if mode=='UDP':
      self.Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    elif mode=='TCP':
      self.Socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    else:
      print('Error : Invalid protocol.\nPlease check your params.')
      sys.exit(1)
    if self.Socket.bind(('127.0.0.1',port)) == -1:
      print('Error : Bind error. Ensure that this port is not used.')
      sys.exit(1)
    self.serverIP=server
    print('The DNS server is running now.')
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
    if self.mode=='TCP':
      self.Socket.listen(MAX_CLIENT)
      while True:
        Clisock,Cliaddr=self.Socket.accept()
        print('Connected with ',Cliaddr)
        thread=TCPconnect(Server_address,Clisock)
        thread.start()
      

        



if __name__ == "__main__":
  protocol=input("Please enter the protocol you want to use : ")
  server=DNS_Server(protocol)
  server.start()
  