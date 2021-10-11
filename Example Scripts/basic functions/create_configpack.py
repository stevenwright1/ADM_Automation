import http.client
import json

sessionid = "_DLWjOpPthPmGTvmemC8M7eqVmLfyFb8vRy6Tb6s0Wc"

target_adc = "g4702445-2286-4b6d-8fb1-c231a0ee17b1"

conn = http.client.HTTPSConnection("adm.cloud.com")
payload = json.dumps({
  "configpack": {
    "targets": [
      {
        "id": target_adc
      }
    ],
    "parameters": {
      "lb-appname": "ApplicationName",
      "lb-virtual-ip": "192.168.50.10",
      "lb-virtual-port": "80",
      "lb-service-type": "HTTP",
      "svc-service-type": "HTTP",
      "svc-servers": [
        {
          "ip": "192.168.5.20",
          "port": 80,
          "add-server": True
        },
        {
          "ip": "192.168.5.21",
          "port": 80,
          "add-server": True
        }
      ],
    }
  }
})
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Cookie': 'NITRO_AUTH_TOKEN=' + sessionid
}
conn.request("POST", "/stylebook/nitro/v1/config/stylebooks/com.citrix.adc.stylebooks/1.1/lb/configpacks", payload, headers)
res = conn.getresponse()
data = res.read()

if res.status != 200:
  print("Error:")
  print("       Status code: " + str(res.status))
  print("       Error payload: " + data)
  exit(1)

payload = json.loads(data, "utf-8")
jobid = payload["configpack"]["job_id"]

print("Configuration Job " + jobid + " has started.")





