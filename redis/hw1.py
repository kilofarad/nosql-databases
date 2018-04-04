from urllib.request import urlopen
import json

url='https://api.nasa.gov/planetary/apod?date=2017-07-08&api_key=3Crutk3oEhkcAKbZCFFPVc6S49hPUaYUdv1gbQAX'
import urllib
import urllib
content=urlopen(url).read()
loaded=json.loads(content.decode('ASCII'))
print(loaded['url'])
