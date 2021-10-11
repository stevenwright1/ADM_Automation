import http.client
import json

sessionid = "_DLWjOpPthPmGTvmemC8M7eqVmLfyFb8vRy6Tb6s0Wc"

base_types = ["string", "ipaddress", "number", "boolean", "tcp-port", "password", "file", "certfile", "keyfile", "certkey", "ipnetwork"]

def get_config_parameters(parameters):
  configpack_params = {}
  for parameter in parameters:
    parameter_name = parameter["name"]
    parameter_type = parameter["type"]
    parameter_required = parameter["required"]

    if parameter_type in base_types:
        if parameter_required:
          parameter_type += "*"
        if parameter_type.endswith("[]"):
          configpack_params[parameter_name] = [parameter_type]
        else:
          configpack_params[parameter_name] = parameter_type
    else:
        if "parameters" in parameter:
          subparameters = parameter["parameters"]
          datatype = get_config_parameters(subparameters)
        else:
          datatype = parameter_type

        if parameter_type.endswith("[]"):
          configpack_params[parameter_name] = [datatype]
        else:
          configpack_params[parameter_name] = datatype

  return configpack_params



conn = http.client.HTTPSConnection("adm.cloud.com")
stylebook = "com.citrix.adc.stylebooks/1.1/lb"
headers = {
  'Cookie': 'NITRO_AUTH_TOKEN= ' + sessionid
}
conn.request("GET", "/stylebook/nitro/v1/config/stylebooks/" + stylebook + "/schema", None, headers)
res = conn.getresponse()
data = res.read()

if res.status != 200:
  print("Error:")
  print("       Status code: " + str(res.status))
  print("       Error payload: " + data)
  exit(1)

schema = json.loads(data, "utf-8")

parameters = schema["schema"]["parameters"]

config_parameters = {
  "parameters": get_config_parameters(parameters)
}

print(json.dumps(config_parameters))
