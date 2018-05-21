import struct
import socket
import lib_Parsers

def Request_builder(PostInfo):
  Request=struct.pack(\
    "!HBBHHHH",\
    PostInfo['ID'],\
    # Since I haven't implement the iterative inquiration...
    # This post MUST BE recursion desired!
    PostInfo['Options']|0x01,\
    PostInfo['Rcode'],\
    PostInfo['QuestionNum'],\
    PostInfo['AnswerNum'],\
    PostInfo['AuthorityNum'],\
    PostInfo['AppendedNum']\
    )
  urls=PostInfo['url']
  for i in range(0,len(urls)):
    question=b''
    url=urls[i]
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
    format="!"+str(len(Request))+'s'+str(len(question))+'sHH'
    Request=struct.pack(format,Request,question,PostInfo['QTYPE'][i],PostInfo['QCLASS'][i])
  return Request



