> ## DNS_server

    This is a simplified DNS server based on python.
    It's binded with '127.0.0.1' by default in order to debug easily.

***
## Features

1. Supports TCP and UDP methods
2. It's multi-threaded with a message Queue
3. Use redis as its database for local cache
4. It's default DNS server is '8.8.8.8'

## Usage

    As this script uses Redis as its cache stroing system ,
    you're required to install Redis to run this program.
    
    Install Redis : pacman -S redis (take arch as an example)
    Install redis.py : check `https://pypi.org/project/redis/`

	`$python DNS_server.py`
	
## Updated

1. Added TCP method
2. Added local cache, but as the AnswerBuilder is not fully developed,
local cache stores AnswerPost instead of IP address.
3. Fixed bug : multi-question post should be answered twice



