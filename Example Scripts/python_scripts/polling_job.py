import http.client
import json

sessionid = "_DLWjOpPthPmGTvmemC8M7eqVmLfyFb8vRy6Tb6s0Wc"
jobid = "958147947"


headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json',
  'Cookie': 'NITRO_AUTH_TOKEN=' + sessionid
}

conn = http.client.HTTPSConnection("adm.cloud.com")

job_status = None

while job_status != "completed" and job_status != "failed":
  conn.request("GET", "/stylebook/nitro/v1/config/jobs/" + jobid, None, headers)
  response = conn.getresponse()
  data = response.read()

  if response.status != 202:
    print("Error:")
    print("       Status code: " + str(response.status))
    print("       Error payload: " + data)
    exit(1)

  payload = json.loads(data, "utf-8")
  job_status = payload["job"]["status"]

config_id = payload["job"]["progress_info"][0]["id"]

if job_status == "completed":
  print("Success: configuration " + config_id + " successully created")
else:
  print("Error: Failed to create configuration.")
  progress_info = payload["job"]["progress_info"]
  for step in progress_info:
      error_details = step["message"]
      print("        " + json.dumps(error_details))
  exit(1)