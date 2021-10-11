import http.client
import json


id = "f20e7432-7a83-416d-a171-9347b92761f4"
secret = "7-rotB6QMFZTuOgpPajPBg=="

conn = http.client.HTTPSConnection("adm.cloud.com")
                 
headers = {
        'isCloud': 'true',
        'Content-Type': 'text/plain',
        'Cookie': ''
  }
request = {
       "login": {
              "ID": id,
              "Secret": secret
       }
}

payload = json.dumps(request)
conn.request("POST", "/nitro/v2/config/login", payload, headers)
response = conn.getresponse()
data = response.read()

if response.status != 200:
  print("Error:")
  print("       Status code: " + str(res.status))
  print("       Error payload: " + data)
  exit(1)


jsondata = json.loads(data)
sessionid = jsondata["login"][0]['sessionid']
print (sessionid)

