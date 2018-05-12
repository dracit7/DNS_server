import struct
import socket
import lib_Parsers

def Request_builder(url,ID):
  question=b''
  QCLASS=1
  QTYPE=1
  while True:
    if url.find('.') != -1:
      length=url.find('.')
    else:
      length=len(url)
    if length==0:
      question+=b'\0'
      break
    question=struct.pack("!"+str(len(question))+"sB",question,length)
    question+=bytes(url[0:length],encoding='utf-8')
    url=url[length+1:]
  Header=struct.pack("!HBBHHHH",ID,1,0,1,0,0,0)
  format="!"+str(len(Header))+"s"+str(len(question))+"sHH"
  Request=struct.pack(format,Header,question,QTYPE,QCLASS)
  print(Request)

print(0x80)


