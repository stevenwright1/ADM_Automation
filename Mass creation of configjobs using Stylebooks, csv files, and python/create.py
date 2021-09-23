#!/usr/bin/python

# Automatic mass creation of LB vServers using Stylebooks
# This script was written to read values from a CSV file and automatically create LB vServers
# The script can be adapted to automate the creation of any Stylebook's configpack

# This script expects an input CSV in Latin1 encoding. If the first entry in your CSV doesn't work, its likely in UTF8.
# Reopen Excel and save the file in "CSV" rather than "CSV (UTF8)" format, alternatively you could use vi to convert it.
# Open the CSV in "vi", press ESC, then enter ":edit ++enc=latin1", press "x" to remove the UTF8 header at the start of file,
# then save the file and quit (ESC, ":wq")

import csv
import http.client
import json

debug = 0

################################
#
#  Set my login variables
#

# You can create an ID and secret by selecting the Identity and Access Management tab in your Cloud portal
id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
secret = "xxxxxxxxxxxxxxxxxxxxxxxx"



def read_csv_file():
    # The CSV file is expected to contain one row for each Stylebook you wish to run and the input parameters in columns
    with open('lbvservers.csv') as file:
        global data_from_csv
        data_from_csv = list(csv.reader(file,delimiter=","))
        i=1
        if debug == 1:
            for each_row_from_the_csv in data_from_csv:
                print 'Here are the columns in row after splitting' + str(i)
                i += 1
                for each_column in each_row_from_the_csv:
                    split_column = each_column.split(":")
                    try:
                        for x in split_column:
                            print (x)
                    except:
                        print "error"



def login_to_ADM(id,secret):
    ################################################
    #
    #  Login to ADM Service and get a session ID
    #
    conn = http.client.HTTPSConnection("netscalermas.cloud.com")
    payload = "{\n \"login\":\n {\n \"ID\":\"" + id + "\",\n \"Secret\":\"" + secret + "\"\n }\n}\n"
    headers = {
      'isCloud': 'true',
      'Content-Type': 'text/plain',
      'Cookie': ''
    }
    conn.request("POST", "/nitro/v2/config/login", payload, headers)
    response = conn.getresponse()
    data = response.read()
    jsondata = json.loads(data)
    global sessionid
    sessionid = jsondata["login"][0]['sessionid']
    customerId = jsondata["login"][0]['customerId']

    if debug == 1:
    	print "\n\nSession established\nSession ID: " + sessionid
    	print "Customer ID: " + customerId




def select_an_ADC(sessionid):
    ################################################
    #
    #  Request a list of ADCs
    #

    conn = http.client.HTTPSConnection("netscalermas.cloud.com")
    payload = ""
    headers = {
      'isCloud': 'true',
      'Content-Type': 'text/plain',
      'Cookie': 'NITRO_AUTH_TOKEN=' + sessionid
    }
    conn.request("GET", "/nitro/v2/config/managed_device", payload, headers)
    response = conn.getresponse()
    data = response.read()
    jsondata = json.loads(data)
    print 'ADC instances located\n'
    for device in jsondata["managed_device"]:
    	name = device['name']
    	ip = device['ip_address']
    	id = device['id']
    	if debug == 1 :
    		print 'Name of instance: ' + name
    		print 'IP address of instance: ' + ip
    		print 'ID of instance: ' + id

    #######################################################################
    #
    #  Ask which ADC you would like to work on and record the instance ID
    #
    i=0
    for device in jsondata["managed_device"]:
    	print str(i+1) + ". " + device['name'] + " - " + device['ip_address'] + " - " + device['id']
    	i += 1

    while True:
        print('Please, select the ADC instance number on which the vServers will be created:')
        response = input()
        if response < 1 or response > i+1:
            print('\nPlease, make a selection from the ADCs listed above.')
            continue
        break
    global selectedadc
    selectedadc = jsondata["managed_device"][response-1]['id']
    if debug == 1: print "You have selected device ID: " + selectedadc


def create_a_config_pack_on_ADM(sessionid,selectedadc,payload):
    headers = {
      'Cookie': 'NITRO_AUTH_TOKEN=' + sessionid,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    }
    conn = http.client.HTTPSConnection("netscalermas.cloud.com")
    if debug == 1: print payload
    # The namespace (com.citrix.adc.stylebooks), version (1.1), and name (lb) used in the URL below are displayed in ADM's list of Stylebooks
    conn.request("POST", "/stylebook/nitro/v1/config/stylebooks/com.citrix.adc.stylebooks/1.1/lb/configpacks", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


def assemble_stylebook_parameters_and_send_to_ADM(data_from_csv,selectedadc):

    ## Start of the Stylebook parameter data
    for each_row_from_the_csv in data_from_csv:

#   Static example configpack payload
#   Here, the values in the configpack will always be the same regardless of the CSV content
#
#    payload =
#   {
#      "configpack": {
#        "targets": [
#          {
#            "id": selectedadc
#          }
#        ],
#        "parameters": {
#          "lb-appname": "Example Application2",
#          "lb-virtual-ip": "192.168.50.90",
#          "lb-virtual-port": 80,
#          "lb-service-type": "HTTP",
#          "svc-service-type": "HTTP",
#          "svc-servers": [
#            {
#              "ip": "192.168.1.10",
#              "port": 80,
#              "add-server": True
#            }
#          ]
#        }
#      }
#    }

#   Simple dynamic example configpack payload
#   Here, the first column of the row (column zero) will be used as the application name
#   The second column of the row (column one) will be used as the virtual IP
#
#    payload =
#   {
#      "configpack": {
#        "targets": [
#          {
#            "id": selectedadc
#          }
#        ],
#        "parameters": {
#          "lb-appname": "''' + each_row_from_the_csv[0] + '''",
#          "lb-virtual-ip": "''' + each_row_from_the_csv[1] + '''",
#          "lb-virtual-port": 80,
#          "lb-service-type": "HTTP",
#          "svc-service-type": "HTTP",
#          "svc-servers": [
#            {
#              "ip": "192.168.1.10",
#              "port": 80,
#              "add-server": True
#            }
#          ]
#        }
#      }
#    }

#


#   Slightly more complex dynamic example configpack payload
#   Here, all of the parameters needed for the Stylebook are taken from the columns of the row
#   Plus, we split column five using ":" as a delimiter and allow for multiple servers

        payload = '''
{
            "configpack":
            {
                "targets": [{"id": "''' + str(selectedadc) + '''"}],
            "parameters":
            {
                "lb-appname": "''' + each_row_from_the_csv[0] + '''",
                "lb-virtual-ip": "''' + each_row_from_the_csv[1] + '''",
                "lb-virtual-port": "''' + each_row_from_the_csv[2] + '''",
                "lb-service-type": "''' + each_row_from_the_csv[3] + '''",
                "svc-service-type": "''' + each_row_from_the_csv[4] + '''",
                "svc-servers": ['''

        ## Expand the list of backend servers to use in StyleBook
        ## Here, we are splitting the servers in column that are separated by a ":"
        split_column = each_row_from_the_csv[5].split(":")
        serverspayload=''
        for each_server in split_column:
            payload = payload + '''
        {
          "ip": "''' + each_server + '''",
          "port": ''' + each_row_from_the_csv[6] + ''',
          "add-server": true
        }'''

        ## End of Stylebook parameter data
        payload = payload + ''']
        }
     }
}
        '''

        ## Create a config pack using the assembled Stylebook parameters from this row
        print "Attempting to create: " + each_row_from_the_csv[0]
        create_a_config_pack_on_ADM(sessionid,selectedadc,payload)



read_csv_file()
login_to_ADM(id,secret)
select_an_ADC(sessionid)
assemble_stylebook_parameters_and_send_to_ADM(data_from_csv, selectedadc)
