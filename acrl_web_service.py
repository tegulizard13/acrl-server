#pip install bottle, requests, gspread
'''
Bottle server with api methods for starting everything
'''
from bottle import Bottle, run, request, template, view
import subprocess
import os
import shutil
import gspread
import time
import logging

# Windows install path and server exe
SERVER_PATH = 'C:\ACServer'
AC_SERVER_EXE = 'acServer.exe'
AC_SERVER_BAT = 'acServer.bat'

# Configuration paths and files
PRESETS_PATH = os.path.join(SERVER_PATH, 'presets')
STAGING_PATH = os.path.join(PRESETS_PATH, 'staging')
CONFIG_PATH = os.path.join(SERVER_PATH, 'cfg')
ENTRY_LIST = 'entry_list.ini'
SERVER_CFG = 'server_cfg.ini'

# HTTP Verbs
POST = "POST"
GET = "GET"
HEAD = "HEAD"

START = 'start'
STOP = 'stop'
RESTART = 'restart'
CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008

# Set up logging, so if something goes wrong there is a file to send to get help.
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
# Log to file
fh = logging.FileHandler('server.log')
fh.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(log_formatter)
# console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
ch.setFormatter(console_formatter)
# Add our handlers to the root logger
root_logger.addHandler(fh)
root_logger.addHandler(ch)

# Our server
acrl = Bottle()


@acrl.route('/about', method=GET)
def home():
    return template('about')


# Check the status and generate an in-depth status page, with links to do things
@acrl.route('/', method=GET)
@view('status')
def status():
    return dict(server_running=server_running())


@acrl.route('/control', method=POST)
def control_server():
    action = request.forms.get('action')
    if action == START:
        start_server()
    elif action == STOP:
        kill_server()
    elif action == RESTART:
        restart_server()
    time.sleep(1)
    return template('redirect_home')


# TODO: add better exception handling
@acrl.route('/upload', method=POST)
def upload_configs():
    entry_list_generated = False
    server_cfg_written = False
    try:
        if not os.path.exists(STAGING_PATH):
            os.makedirs(STAGING_PATH)

        server_cfg = request.files.get('server_cfg')
        entry_list = request.files.get('entry_list')

        # Attempt to write the uploaded server config to the staging directory
        server_config_path = os.path.join(STAGING_PATH, server_cfg.filename)
        server_cfg.save(server_config_path, overwrite=True)
        server_cfg_written = True

        # Attempt to write the uploaded entry list to the staging directory
        entry_list_path = os.path.join(STAGING_PATH, entry_list.filename)
        entry_list.save(entry_list_path, overwrite=True)
        entry_list_generated = True

        # Copy the new configs to the active config directory
        shutil.copy(server_config_path,
                    os.path.join(CONFIG_PATH, SERVER_CFG))
        shutil.copy(entry_list_path,
                    os.path.join(CONFIG_PATH, ENTRY_LIST))
    except Exception as e:
        logging.exception(e.message)
        logging.exception('Continuing to load, new uploads required.')
    return template('upload_status',
                    server_cfg_written=server_cfg_written,
                    entry_list_generated=entry_list_generated)


# Start the server process
def start_server():
    os.chdir(SERVER_PATH)
    # If Eu (or if the bat file exists, run stracker
    if os.path.isfile(os.path.join(SERVER_PATH, 'stracker.bat')):
        p = subprocess.Popen(['stracker.bat', 'arg1', 'arg2'],
                             close_fds=True,
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
    # Run the ACRL Plugin for GT3
    # TODO: update so gt3 values are not hardcoded in
    p = subprocess.Popen(['ACRL_Plugin.exe', '60', '15', 'standing'],
                         close_fds=True,
                         creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
    time.sleep(1)
    # TODO: For now call the bat file so the log gets created for us
    p = subprocess.Popen([AC_SERVER_BAT],
                         close_fds=True,
                         creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)

    # file modification date and pid are stored
    with open(os.path.join(CONFIG_PATH, 'PID'), 'w') as pid_file:
        pid_file.write(str(p.pid))
 
    # Return True if server is running (may be misleading)
    return server_running()


# Fragile if you rely on the PID file. Scorched earth, motherfucker.
def kill_server():
    p = subprocess.Popen(["cmd", "/C", "tasklist"], stdout=subprocess.PIPE)
    output = p.communicate()[0]
    # Get a list of acrl server (acServer.exe) pids
    ac_server_pids = [name.split()[1] for name in output.strip().split('\n') if name.split()[0] == AC_SERVER_EXE]
    for pid in ac_server_pids:
        k = subprocess.Popen(["cmd", "/C", "taskkill", "/PID", str(pid), "/f"], stdout=subprocess.PIPE)

    # Return True if the server is stopped
    if not server_running():
        #TODO: upload logs here?
        return True
    return False


def restart_server():
    if not kill_server():
        return False
    time.sleep(1)
    return start_server()


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
# TODO: Finish implementing at some point
def current_entry_list(checkin_url):
    # Get the check-in list from google sheets. use gspread
    checkin_list = [] #list of username strings who checked in

    gc = gspread.authorize(credentials)
    # Open a worksheet from spreadsheet with one shot
    wks = gc.open("Where is the money Lebowski?").sheet1
    wks.update_acell('B2', "it's down there somewhere, let me take another look.")
    # Fetch a cell range
    cell_list = wks.range('A1:B7')

    # Get the full entry list of all members (also store as a google doc?)
    racers = {'example_racer_name': 'full_entry_as_string'}

    entries = []
    for checked_in in checkin_list:
        entries.append(racers[checked_in])

    return "\n\n".join(entries)


# Writes unsafely to the current config directory
def write_current_entry_list(entry_list_string):
    p1 = subprocess.Popen(["cmd", "/C", "DIR /B", PRESETS_PATH], stdout=subprocess.PIPE)
    output = sorted(p1.communicate()[0])
    server_config_dir_name = output[0]
    with open(os.path.join(PRESETS_PATH, server_config_dir_name, ENTRY_LIST), 'w') as entry_list_ini:
        entry_list_ini.write(entry_list_string)

if __name__ == "__main__":
    run(acrl, host='0.0.0.0', port=8080)
