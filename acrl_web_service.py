'''
Bottle server with api methods for starting everything
'''
# TODO: make templates and render some html.
from bottle import Bottle, run, request, template, view #pip install bottle
import subprocess
import os
import gspread #pip install gspread

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


@acrl.route('/about', method=GET)
def home():
    return "Welcome to ACRL"


# Check the status and generate an in-depth status page, with links to do things
@acrl.route('/', method=GET)
@view('status')
def status():
    return dict(server_running=server_running())


@acrl.route('/upload', method=GET)
@view('upload')
def upload_configs_page():
    pass


# TODO: add exception handling
@acrl.route('/upload', method=POST)
def upload_configs():
    entry_list_generated = False
    server_cfg_written = False

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
    server_cfg_written = True

    # Get the new checkin list into the same directory
    current_entries = current_entry_list(check_in_sheet_url)
    write_current_entry_list(current_entries)
    entry_list_generated = True

    return template('upload_status',
                    server_cfg_written=server_cfg_written,
                    entry_list_generated=entry_list_generated)


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
# TODO: Finish implementing
def current_entry_list(checkin_url):
    # Get the check-in list from google sheets. use gspread
    checkin_list = [] #list of username strings who checked in

    # Get the full entry list of all members (also store as a google doc?)
    racers = {'example_racer_name': 'full_entry_as_string'}

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