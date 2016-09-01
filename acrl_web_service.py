#pip install bottle, requests, gspread

'''
Bottle server with api methods for starting everything
'''
# TODO: make templates and render some html.
from bottle import Bottle, run, request, template, view #pip
import subprocess
import os
import shutil
import gspread #pip install gspread

# Windows install path containing server exe
# SERVER_PATH = 'C:\Program Files (x86)\Steam\steamapps\common\\assettocorsa\server'
SERVER_PATH = 'C:\ACServer'
CONFIG_PATH = os.path.join(SERVER_PATH, 'presets')
# Runnable cfg
CFG_PATH = os.path.join(SERVER_PATH, 'cfg')
AC_SERVER_EXE = 'acServer.exe'
AC_SERVER_BAT = 'acServer.bat'
ENTRY_LIST = 'entry_list.ini'
SERVER_CFG = 'server_cfg.ini'

# HTTP Verbs
POST = "POST"
PUT = "PUT"
GET = "GET"
HEAD = "HEAD"
DELETE = "DELETE"

START = 'start'
STOP = 'stop'
RESTART = 'restart'
CREATE_NEW_PROCESS_GROUP = 0x00000200
DETACHED_PROCESS = 0x00000008

# Our server
acrl = Bottle()


@acrl.route('/about', method=GET)
def home():
    return "Welcome to ACRL!<br />" \
           "ACRL is an international racing league that was created to provide clean and competitive multiplayer " \
           "racing in Assetto Corsa. The league is divided into North American and European subleagues to better " \
           "serve our members. If that sounds like something you are interested in, go ahead and register with our " \
           "league!"


# Check the status and generate an in-depth status page, with links to do things
@acrl.route('/', method=GET)
@view('status')
def status():
    return dict(server_running=server_running())


# TODO: add exception handling
@acrl.route('/upload', method=POST)
def upload_configs():
    #entry_list_generated = False
    server_cfg_written = False

    server_cfg = request.files.get('server_cfg')
    entry_list = request.files.get('entry_list')
    # check_in_sheet_url = request.forms.get('check_in_sheet_url')

    # List CONFIG_PATH, and make the next directory
    p1 = subprocess.Popen(["cmd", "/C", "DIR /B", CONFIG_PATH], stdout=subprocess.PIPE)
    output = sorted(p1.communicate()[0])
    server_config_dir = output[0]
    next_server_config_dir = "{}{}".format(server_config_dir[:-2], int(server_config_dir[-2:])+1)

    if not os.path.exists(os.path.join(CONFIG_PATH, next_server_config_dir)):
        os.makedirs(os.path.join(CONFIG_PATH, next_server_config_dir))

    server_config_path = os.path.join(CONFIG_PATH, next_server_config_dir, server_cfg.filename)
    entry_list_path = os.path.join(CONFIG_PATH, next_server_config_dir, entry_list.filename)
    server_cfg.save(server_config_path)
    entry_list.save(entry_list_path)
    server_cfg_written = True

    # Get the new checkin list into the same directory
    # current_entries = current_entry_list(check_in_sheet_url)
    # write_current_entry_list(current_entries)
    entry_list_generated = True

    # Copy the configs to the runnable dir
    p1 = subprocess.Popen(["cmd", "/C", "DIR /B", CONFIG_PATH], stdout=subprocess.PIPE)
    output = sorted(p1.communicate()[0])
    server_config_dir_name = output[0]
    # Copy the server config
    shutil.copy(server_config_path,
                os.path.join(CFG_PATH, SERVER_CFG))
    # Copy the entry list
    shutil.copy(entry_list_path,
                os.path.join(CFG_PATH, ENTRY_LIST))
    # shutil.copy(os.path.join(CONFIG_PATH, server_config_dir_name, ENTRY_LIST),
    #             os.path.join(CFG_PATH, ENTRY_LIST))

    return template('upload_status',
                    server_cfg_written=server_cfg_written,
                    entry_list_generated=entry_list_generated)


@acrl.route('/control', method=POST)
def control_server():
    action = request.forms.get('action')
    if action == START:
        start_server()
    elif action == STOP:
        kill_server()
    elif action == RESTART:
        restart_server()
    return status()


# TODO: start the server and return the process id
# TODO: Found this on SO, need to verify the server keeps going if the web service dies
# I don't know how long this blocks for
def start_server():
    ac_path = '"{}"'.format(os.path.join(SERVER_PATH, AC_SERVER_EXE))
    os.chdir(SERVER_PATH)
    # TODO: For now call the bat file so the log gets created for us.
    p = subprocess.Popen([AC_SERVER_BAT],
                         close_fds=True,
                         creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)

    # file modification date and pid are stored
    with open(os.path.join(CFG_PATH, 'PID'), 'w') as pid_file:
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
        #TODO: upload logs
        return True
    return False


def restart_server():
    if not kill_server():
        return False
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
# TODO: Finish implementing
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
    p1 = subprocess.Popen(["cmd", "/C", "DIR /B", CONFIG_PATH], stdout=subprocess.PIPE)
    output = sorted(p1.communicate()[0])
    server_config_dir_name = output[0]
    with open(os.path.join(CONFIG_PATH, server_config_dir_name, ENTRY_LIST), 'w') as entry_list_ini:
        entry_list_ini.write(entry_list_string)

if __name__ == "__main__":
    run(acrl, host='0.0.0.0', port=8080)