#!/usr/local/bin/python3

# Automatic mass creation of LB vServers using Stylebooks
# This script was written to read values from a CSV file and template and then automatically create LB vServers
# The template can be adapted to automate the creation of any Stylebook's configpack

# This script expects an input CSV in Latin1 encoding. If the first entry in your CSV doesn't work, its likely in UTF8.
# Reopen Excel and save the file in "CSV" rather than "CSV (UTF8)" format, alternatively you could use vi to convert it.
# Open the CSV in "vi", press ESC, then enter ":edit ++enc=latin1", press "x" to remove the UTF8 header at the start of file,
# then save the file and quit (ESC, ":wq")

# This script also expects a text template. The template should list a placeholder name for CSV column (in order and without
# any hyphens in the placeholder names). Loops within the template can be started using "<% for server in svcservers %>" and
# ended by using <% endfor %>

# This script uses Python3 and required jinja2. For macOS, the following commands may assist you
# brew install python
# which python3 (ensure the path to python matches the alias)
# echo "alias python=/usr/local/bin/python3" >> ~/.zshrc
# curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
# python get-pip.py
# pip install jinja2

import argparse
import re
import csv
import http.client
import json
from jinja2 import Environment, PackageLoader, select_autoescape, BaseLoader

debug = 0

#  Set my login variables for ADM
# You can create an ID and secret by selecting the Identity and Access Management tab in your Cloud portal
id = "1707d2ff-e200-46be-848a-93faf2076d6b"
secret = "DIH1CzF_GSZG2zNnEVShLA=="

# Define template variables
environment = Environment(
    block_start_string='<%',
    block_end_string='%>',
    variable_start_string='<<',
    variable_end_string='>>'
)


def parse_csv_template(template_path):
    ################################################
    #
    #  The CSV file is expected to contain one row for each Stylebook you wish to run and the input parameters in columns
    #
    with open(template_path, "r") as f:
        data = f.read()
        placeholders = []
        stage = 0
        template = ""
        stylebook = ""
        for line in data.splitlines():
            if line == "STYLEBOOK NAMESPACE/VERSION/STYLEBOOK":
                stage = 1
                continue

            if stage == 1 and line !="" and line !="CSV COLUMNS":
                stylebook = line

            if line == "CSV COLUMNS":
                stage = 2
                continue

            if stage == 2 and line and line != "TEMPLATE":
                placeholders.append(line)
                continue

            if stage == 2 and line == "TEMPLATE":
                stage = 3
                continue

            if stage == 3:
                template += line + "\n"

        return stylebook, placeholders, re.sub(r'<<\s*,\s*>>', '<< "," if not loop.last >>', template)


def login_to_ADM(id, secret):
    ################################################
    #
    #  Login to ADM Service and get a session ID
    #
    conn = http.client.HTTPSConnection("netscalermas.cloud.com")
    payload = "{\n \"login\":\n {\n \"ID\":\"" + id + \
        "\",\n \"Secret\":\"" + secret + "\"\n }\n}\n"
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
        print("\n\nSession established\nSession ID: " + sessionid)
        print("Customer ID: " + customerId)


def show_job_result(stylebook,jobid):
    conn = http.client.HTTPSConnection("netscalermas.cloud.com")
    payload = ""
    headers = {
        'isCloud': 'true',
        'Content-Type': 'text/plain',
        'Cookie': 'NITRO_AUTH_TOKEN=' + sessionid
    }
    conn.request("GET", "https://netscalermas.cloud.com/stylebook/nitro/v1/config/stylebooks/" + stylebook + "/jobs/" + jobid, payload, headers)
    response = conn.getresponse()
    data = response.read()
    print (data)



def select_an_ADC(sessionid):
    ################################################
    #
    #  Request and display a list of ADCs
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
    print('The following ADC instances IDs can be referenced within your CSV file.\nName - IP address - ID for use in CSV.\n')
    for device in jsondata["managed_device"]:
        name = device['name']
        ip = device['ip_address']
        id = device['id']
    i = 0
    for device in jsondata["managed_device"]:
        print(str(i + 1) + ". " + device['name'] + " - " +
              device['ip_address'] + " - " + device['id'])
        i += 1


def create_a_config_pack_on_ADM(sessionid, payload, stylebook):
    headers = {
        'Cookie': 'NITRO_AUTH_TOKEN=' + sessionid,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    conn = http.client.HTTPSConnection("netscalermas.cloud.com")
    if debug == 1:
        print(payload)
    # The namespace (com.citrix.adc.stylebooks), version (1.1), and name (lb) used in the URL below are displayed in ADM's list of Stylebooks
    conn.request(
        "POST", "/stylebook/nitro/v1/config/stylebooks/" + stylebook + "/configpacks", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


list_type = re.compile(r'^\s*([A-z]+[\d\w_]*)\s*:\s*list\s*$')
primitive_type = re.compile(r'^\s*([A-z]+[\d\w_]*)\s*$')


def parse_template(placeholders, data, template):
    if len(data) == 0:
        raise ValueError("CSV file is empty.")

    def preprocess_header(value):
        match = list_type.search(value)
        if match:
            return match.group(1), True

        match = primitive_type.search(value)
        if match:
            return match.group(1), False

        raise ValueError(f"Invalid column header: {value}")

    def preprocess_cell(value, is_list):
        if is_list:
            return value.split(":")
        return value

    for row in data:
        if len(placeholders) != len(row):
            raise ValueError(
                f"Template does not include same amount of placeholders as there are columns in the CSV.\nPlaceholders: {placeholders}\nRow: {row}")

        context = {}
        for placeholder, cell in zip(placeholders, row):
            value, is_list = preprocess_header(placeholder)
            context[value] = preprocess_cell(cell, is_list)

        rtemplate = environment.from_string(template)
        string = rtemplate.render(**context)
        try:
            json.loads(string)
        except Exception as e:
            raise ValueError(f"Result is not valid JSON.\n{string}")
        yield string


def load_data(fn):
    with open(fn, 'r', newline='\n') as f:
        return list(csv.reader(f, delimiter=','))


def run(csv_path, template_path):
    stylebook, placeholders, template = parse_csv_template(template_path)
    csv_data = load_data(csv_path)
    login_to_ADM(id, secret)
    i=1
    for payload in parse_template(placeholders, csv_data, template):
        print ("\nCreating ADM Config Pack based on CSV row: " + str(i))
        create_a_config_pack_on_ADM(sessionid, payload, stylebook)
        i += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--csv', help='Path to CSV file.',
                        required=False,  default="lbvservers.csv")
    parser.add_argument('-t', '--template', help='Path to template file.',
                        required=False, default="template.txt")
    parser.add_argument('-a', '--showadcs', help='Show a list of ADCs and their target IDs',
                        required=False, action='store_true')
    parser.add_argument('-j', '--showjob', nargs=2, help='Show the result of a job_id number',
                        required=False, default='')
    args = parser.parse_args()
    if args.showadcs:
        login_to_ADM(id, secret)
        select_an_ADC(sessionid)
    if args.showjob:
        print (args.showjob[0])
        print (args.showjob[1])
        login_to_ADM(id, secret)
        show_job_result(args.showjob[0],args.showjob[1])
    else:
        run(args.csv, args.template)
