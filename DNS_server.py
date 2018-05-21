# A simplified DNS server with cache.

# import libs
import sys
import socket
import struct
import threading
import queue
import redis

from lib_Parsers import RequestParser
from lib_Parsers import AnswerParser
from lib_Builders import Request_builder

MAX_SIZE=4096
MAX_CLIENT=5
DATABASE_NAME='DNS_server_cache'
IP_BINDING='127.0.0.1'
AnswerQueue=queue.Queue()

class SendRequest(threading.Thread):
  def __init__(self,post,servaddr,cliaddr):
    threading.Thread.__init__(self)
    try:
      self.cache=redis.Redis(host='127.0.0.1',port=6379,db=0)
    except:
      print('Error : redis error. Cannot connect to the redis server.')
      sys.exit()
    try:
      self.Sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    except:
      print("Error : failed to create a UDP socket.")
      sys.exit()
    self.PostContext=post
    self.Servaddress=servaddr
    self.Clientaddress=cliaddr
  def run(self):
    try:
      url=RequestParser(self.PostContext)['url']
      # We need to confirm how many Questions are there
      # in order to know there'll be how many answers.
      QuestionNum=RequestParser(self.PostContext)['QuestionNum']
    except:
      print("Error : parse error. Maybe parse function has some problem.")
      sys.exit()
    # Check if this url is cached.
    cached=True
    for i in range(0,QuestionNum):
      if self.cache.hexists(DATABASE_NAME,url[i]) == 0:
        cached=False
    if cached == True:
      # if cached, put the answer in cache straightly to answerqueue.
      for i in range(0,QuestionNum):
        AnswerQueue.put((self.cache.hget(DATABASE_NAME,url[i]),self.Clientaddress))
    else:
      # if not, get the answer from the upper DNS server
      # and cache the answer to redis.
      self.Sock.sendto(self.PostContext,self.Servaddress)
      for i in range(0,QuestionNum):
        Answer=self.Sock.recv(MAX_SIZE)
        self.cache.hset(DATABASE_NAME,url[i],Answer)
        AnswerQueue.put((Answer,self.Clientaddress))

class SendAnswer(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    try:
      self.Sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    except:
      print("Error : failed to create a UDP socket.")
      sys.exit()
  def run(self):
    # As long as the Answer queue is not empty,
    # get answer post from it and send it to the certain client.
    while True:
      if AnswerQueue.empty() == False:
        Post,Cliaddr=AnswerQueue.get()
        self.Sock.sendto(Post,Cliaddr)
        print('Sent answer to ',Cliaddr)

class TCPconnect(threading.Thread):
  def __init__(self,servaddr,Clisock):
    threading.Thread.__init__(self)
    try:
      self.Serversock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    except:
      print("Error : failed to create a UDP socket.")
      sys.exit()
    self.Clientsock=Clisock
    self.servaddr=servaddr
  def run(self):
    # After building the TCP connection with a client,
    # Open a new thread to transfer infomation.
    try:
      Post=self.Clientsock.recv(MAX_SIZE)
      self.Serversock.sendto(Post,self.servaddr)
      Post=self.Serversock.recv(MAX_SIZE)
      self.Clientsock.send(Post)
      self.Clientsock.close()
    except:
      print('Error : connection error. Failed to convert infomation.')
      pass
    print('Connection closed.')

class DNS_Server:
  # Use Google DNS server (8.8.8.8) as default upper server
  def __init__(self,mode='UDP',server="8.8.8.8",port=9190):
    self.mode=mode
    # Support both TCP and UDP requests
    try:
      if mode=='UDP':
        self.Socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
      elif mode=='TCP':
        self.Socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
      else:
        print('Error : Invalid protocol. Please check your params.')
        sys.exit()
      self.Socket.bind(('127.0.0.1',port))
    # Bind to a address to ensure that client's request can be accepted.
    # If necessary, change this address.
    except:
      print('Error : Bind error. Ensure that this port is not used.')
      sys.exit()
    self.serverIP=server
    print('The DNS server is running now.')
  def start(self):
    Server_address=(self.serverIP,53)
    if self.mode=='UDP':
      # Use Answer thread to send answer to clients.
      try:
        Answer_thread=SendAnswer()
        Answer_thread.start()
      except:
        print("Error : Thread error. Something happened while starting a thread.")
        sys.exit()
      while True:
        # Firstly get requests from clients
        Post,Cliaddr=self.Socket.recvfrom(MAX_SIZE)
        print('Get DNS request from ',Cliaddr)
        # If I have to write the request post by my self,
        # Uncomment following two lines:
        PostInfo=RequestParser(Post)
        Post=Request_builder(PostInfo)

        # Send the request to upper server
        try:
          Request_thread=SendRequest(Post,Server_address,Cliaddr)
          Request_thread.start()
        except:
          print("Error : Thread error. Something happened while starting a thread.")
          sys.exit()
    if self.mode=='TCP':
      # Accept TCP connection requests
      try:
        self.Socket.listen(MAX_CLIENT)
      except:
        print("Error : Listen error.")
        sys.exit()
      while True:
        try:
          Clisock,Cliaddr=self.Socket.accept()
        except:
          print("Error : accept error.")
          sys.exit()
        print('Connected with ',Cliaddr)
        try:
          thread=TCPconnect(Server_address,Clisock)
          thread.start()
        except:
          print("Error : Thread error. Something happened while starting a thread.")
          sys.exit()
      

        



if __name__ == "__main__":
  try:
    protocol=input("Please enter the protocol you want to use : ")
    server=DNS_Server(protocol)
    server.start()
  except KeyboardInterrupt:
    print("Please press Ctrl+C again.")
    exit(0)
  
  