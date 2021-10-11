import http.client
import json

sessionid = "_DLWjOpPthPmGTvmemC8M7eqVmLfyFb8vRy6Tb6s0Wc"

conn = http.client.HTTPSConnection("adm.cloud.com")
headers = {
        'isCloud': 'true',
        'Content-Type': 'text/plain',
        'Cookie': 'NITRO_AUTH_TOKEN=' + sessionid
    }
conn.request("GET", "/nitro/v2/config/managed_device", None, headers)
response = conn.getresponse()
data = response.read()

if response.status != 200:
  print("Error:")
  print("       Status code: " + str(response.status))
  print("       Error payload: " + data)
  exit(1)

jsondata = json.loads(data)
print('\n\nHere is a list of ADCs.\n')
for device in jsondata["managed_device"]:
        name = device['hostname']
        ip = device['ip_address']
        id = device['id']
        type = device['type']
        status = device['status']
        if status == "Success":
                print (name + " " + ip + " " + id + " " + type)

