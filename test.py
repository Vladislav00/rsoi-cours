from http import client
import json
import uuid
import urllib
import jwt
import random
import string

login = 'FabricUH'
password = 'YEXAuIeMijIc3O8'

c = client.HTTPConnection('localhost')

chars = string.digits + string.ascii_uppercase

c.request("POST", "/auth/login", json.dumps({'login':login, 'password':password}))
r = c.getresponse()
print("Authorize:")
print(r.status)
if r.status == 302:
	token =  urllib.parse.parse_qs(urllib.parse.urlparse(r.headers['Location']).query)['auth_token'][0]
	payload = jwt.decode(token,verify=False)
	pr = payload['Username'][-2:]
	
	num = random.randrange(1, 10)
	codes = []
	for i in range(num):
		code = pr+"".join([random.choice(chars) for j in range(6)])
		print(code)
		codes.append(code)	
	c.request("POST", "/code", json.dumps(codes), headers={"AUTHORIZATION": token})
	r = c.getresponse()
	if r.status == 200:
		print(success)
	else:
		print(r.read())
