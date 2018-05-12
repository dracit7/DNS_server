# Parser functions.
import struct
import socket

def RequestParser(Post):
  PostInfo={}
  Header=struct.unpack("!HBBHHHH",Post[:12])
  Question=Post[12:]
  # ID : a random number to match requests and answers
  PostInfo['ID']=Header[0]
  # Options: 
  # +----+------+----+----+----+
  # | 1  |   4  | 1  |  1 |  1 |
  # | QR |Opcode| AA | TC | RD |
  # +----+------+----+----+----+
  # QR : 0 for Question, 1 for Answer
  # Opcode : 0-QUERY 1-IQUERY 2-STATUS (0 usually)
  # AA : Authoratitive Answer (Only meaningful in Answer)
  # TC : TrunCationed (If post is too long it would be truncationed)
  # RD : Recursion Desired (Only meaningful in Request)
  PostInfo['Options']=Header[1]
  # Rcode (actually not only Rcode, but it can't be divided in python):
  # +----+------+----+----+----+
  # | 1  |   3  |      4       |
  # | RA | zero |    rcode     |
  # +----+------+----+----+----+
  # RA : Recursion Available (Only meaningful in Answer)
  # zero : must be zero
  # rcode : Error code (Only meaningful in Answer)
  PostInfo['Rcode']=Header[2]
  # Four unsigned short variables are used to present number of details
  PostInfo['QuestionNum']=Header[3]
  PostInfo['AnswerNum']=Header[4]
  PostInfo['AuthorityNum']=Header[5]
  PostInfo['AppendedNum']=Header[6]
  if PostInfo['Options'] & 0b10000000 == 0:
    # Parse Question
    url=[]
    for i in range(0,PostInfo['QuestionNum']):
      Domainname=''
      while True:
        length=Question[0]
        Domainname+=str(Question[1:length+1],encoding='utf-8')
        if length != 0:
          Domainname+='.'
          Question=Question[length+1:]
        else:
          Question=Question[1:]
          break
      url.insert(0,Domainname)
      # OtherInfo=struct.unpack("!HH",Question[:4])
      # QTYPE=OtherInfo[0]
      # QCLASS=OtherInfo[1]
      Question=Question[4:]
    PostInfo['url']=url
    return PostInfo
  else:
    print("Error : This is not request")
    exit(1)

def ParseOffset(Post,ptr):
  Name=''
  while True:
    flag=Post[ptr]
    if flag==0:
      break
    # The first two bits are '11'
    # Which represents "offset pointer"
    # The bits following means how many bytes the OFFSET is.
    if flag & 0b11000000 == 0b11000000:
      step = struct.unpack('!H',Post[ptr:ptr+2])[0] & 0b0011111111111111
      Name+=ParseOffset(Post,step)
      break
    else:
      Name+=str(Post[ptr+1:ptr+flag+1],encoding='utf-8')
      ptr+=flag+1
      if flag != 0:
        Name+='.'
  return Name

def AnswerParser(Post):
  PostInfo={}
  # Use a pointer to represent position
  ptr=12

  print(Post)
  Header=struct.unpack("!HBBHHHH",Post[:12])
  PostInfo['ID']=Header[0]
  PostInfo['Options']=Header[1]
  PostInfo['Rcode']=Header[2]
  PostInfo['QuestionNum']=Header[3]
  PostInfo['AnswerNum']=Header[4]
  PostInfo['AuthorityNum']=Header[5]
  PostInfo['AppendedNum']=Header[6]
  PostInfo['Answers']=[]

  if PostInfo['Options'] & 0b10000000 == 0b10000000:
    # Parse Answer
    for i in range(0,PostInfo['QuestionNum']):
      # Skip Questions
      while True:
        len=Post[ptr]
        ptr+=len+1
        if len==0:
          break
      # Skip QTYPE and QCLASS
      ptr+=4
    for i in range(0,PostInfo['AnswerNum']):
      DomainName=ParseOffset(Post,ptr)
      ptr+=2
      TYPEandCLASS=struct.unpack('!HH',Post[ptr:ptr+4])
      ptr+=4
      # TIMETOLIVE=struct.unpack('!I',Post[ptr:ptr+4])
      ptr+=4
      LENGTH=struct.unpack('!H',Post[ptr:ptr+2])
      ptr+=2

      TYPE=TYPEandCLASS[0]
      # if TYPE == DNS_A:
      # That means the answer is the IP address of the domainname.
      if TYPE == 1:
        if LENGTH[0] == 4:
          RAWIP=Post[ptr:ptr+LENGTH[0]]
          IP=socket.inet_ntoa(RAWIP)
          PostInfo['Answers']+={"Domain Name:",DomainName,"IP address:",IP}
      # if TYPE == DNS_CLASS:
      # That means the answer is the alias name of the domainname.
      elif TYPE == 5:
        ALIAS=ParseOffset(Post,ptr)
        PostInfo['Answers']+={"Domain Name:",DomainName,"Alias Name:",ALIAS}
      ptr+=LENGTH[0]
  return PostInfo

