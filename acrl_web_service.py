'''
Bottle server with api methods for starting everything
'''
# TODO: make templates and render some html.
from bottle import Bottle, run, request
import subprocess
import os

# Windows install path containing server exe
SERVER_PATH = 'C:\\acrl\\'
CONFIG_PATH = os.path.join(SERVER_PATH, 'presets')
AC_SERVER_EXE = 'acServer.exe'
ENTRY_LIST = 'entry_list.ini'

# HTTP Verbs
POST = "POST"
PUT = "PUT"
GET = "GET"
HEAD = "HEAD"
DELETE = "DELETE"

#
# Our server
acrl = Bottle()


@acrl.route('/home', method=GET)
def home():
    return "Welcome to ACRL"


# Check the status and generate an in-depth status page
@acrl.route('/status', method=GET)
def status():
    acrl_status = "You're seeing this, so the Amazon EC2 Instance is on!\n"
    if server_running():
        acrl_status = "{}The race server should be up and running!\n".format(acrl_status)
    else:
        acrl_status = "{}The race server is not running.\n".format(acrl_status)
    return acrl_status

# TODO: all these returns will have to be redone using templates
@acrl.route('/upload', method=POST)
def upload_configs():
    upload = request.files.get('server_cfg')
    check_in_sheet_url = request.forms.get('check_in_sheet_url')

    # List CONFIG_PATH, and make the next directory
    p1 = subprocess.Popen(["cmd", "/C", "DIR /B", CONFIG_PATH], stdout=subprocess.PIPE)
    output = sorted(p1.communicate()[0])
    server_config_dir = output[0]
    next_server_config_dir = "{}{}".format(server_config_dir[:-2], int(server_config_dir[-2:])+1)

    if not os.path.exists(os.path.join(CONFIG_PATH, next_server_config_dir)):
        os.makedirs(os.path.join(CONFIG_PATH, next_server_config_dir))

    file_path = os.path.join(CONFIG_PATH, next_server_config_dir, upload.filename)
    upload.save(file_path)

    return "File successfully saved to '{0}'.".format(file_path)


# lol
def instance_running():
    return True


# Check to see if the server exe is in the list of running programs
def server_running():
    server_is_running = False
    # Remember, this part is Windows only
    p1 = subprocess.Popen(["cmd", "/C", "tasklist"], stdout=subprocess.PIPE)
    output = p1.communicate()[0]
    # Get a list of process names
    programs_running = [name.split()[0] for name in output.strip().split('\n')]
    if "acServer.exe" in programs_running:
        server_is_running = True
    return server_is_running


# Returns new entry list as a string
# TODO: Implement
def current_entry_list(checkin_url):
    # Get the check-in list from google sheets
    checkin_list = []

    # Get the full entry list of all members (also store as a google doc?)
    racers = {'name': 'entry_string'}

    entries = []
    for checked_in in checkin_list:
        entries.append(racers[checked_in])

    return "\n\n".join(entries)


# Writes unsafely to the current config directory
def write_current_entry_list(entry_list_string):
    p1 = subprocess.Popen(["cmd", "/C", "DIR /B", CONFIG_PATH], stdout=subprocess.PIPE)
    output = sorted(p1.communicate()[0])
    server_config_dir_name = output[0]
    with open(os.path.join(CONFIG_PATH, server_config_dir_name, ENTRY_LIST), 'w') as entry_list_ini:
        entry_list_ini.write(entry_list_string)

if __name__ == "__main__":
    run(acrl, host='127.0.0.1', port=8080)