# TODO: Process handling using PIDs to support multiple servers on one machine
# TODO: Fix logging so that it works correctly, it isn't logging now...
# TODO: Links to race log files for after the race.
# TODO: Multi-server support

#pip install bottle, requests, gspread
"""
Bottle server with api methods for starting everything
"""
import argparse
import logging
import os
import shutil
import subprocess
import time

import gspread
from bottle import Bottle, run, request, template, view


"""
folders: EU1, EU2, EU3, EU4 in C:\Users\Administrator\Desktop\


"""





# Configuration paths and files
SERVER_PATH = 'C:\Users\Administrator\Desktop'
PRESETS_PATH = os.path.join(SERVER_PATH, 'presets')
STAGING_PATH = os.path.join(PRESETS_PATH, 'staging')
CONFIG_PATH = os.path.join(SERVER_PATH, 'cfg')
ENTRY_LIST = 'entry_list.ini'
SERVER_CFG = 'server_cfg.ini'

CUT_PLUGIN_PATH = os.path.join(SERVER_PATH, 'CutPlugin')
AC_SERVER_BAT = 'acServer.bat'

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


class ServerApp(object):
    def __init__(self):
        self._base_path = 'C:\Users\Administrator\Desktop'
        self.pid = None
        self.directory = None
        self.executable = None
        self.launcher = None

    @property
    def executable_path(self):
        path_parts = [self._base_path,
                      self.directory if self.directory else '',
                      self.executable]
        full_path = os.path.join(*path_parts)
        return full_path

    def run(self):
        pass


class ACServer(ServerApp):
    def __init__(self):
        super(ACServer, self).__init__()
        self.executable = 'acServer.exe'
        self.launcher = 'Start - Server.bat'


class Stracker(ServerApp):
    def __init__(self):
        super(Stracker, self).__init__()
        self.executable = 'stracker.exe'
        self.launchers = ['Start - Plugin - Stracker - L1.bat',
                          'Start - Plugin - Stracker - L2.bat',
                          'Start - Plugin - Stracker - L3.bat']
        self.launcher = ''


class RollingStartPlugin(ServerApp):
    def __init__(self):
        super(RollingStartPlugin, self).__init__()
        self.executable = 'RollingStartPlugin.exe'
        self.launcher = 'Start - Plugin - Rolling L2.bat'


class CutPlugin(ServerApp):
    def __init__(self):
        super(CutPlugin, self).__init__()
        self.executable = 'ACCutDetectorPlugin.exe'
        self.launcher = 'Start - Plugin - Cut - L1.bat'


class ACRLServer(object):
    def __init__(self, http_port):
        self.http_port = http_port

    # Start the server processes
    def start_server(self):
        os.chdir(SERVER_PATH)
        # If Eu (or if the bat file exists, run stracker)
        if os.path.isfile(os.path.join(SERVER_PATH, 'start-stracker.cmd')):
            p = subprocess.Popen(['start-stracker.cmd'],
                                 close_fds=True,
                                 creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        time.sleep(1)
        server_pids[STRACKER_EXE] = p.pid

        # Run the ACRL Plugin for GT3
        # TODO: update so gt3 timing values are not hardcoded in
        p = subprocess.Popen([ACRL_PLUGIN_EXE, '60', '15', 'standing'],
                             close_fds=True,
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        time.sleep(1)
        server_pids[ACRL_PLUGIN_EXE] = p.pid

        # Run ACCutDetectorPlugin.exe in CutPlugin folder
        os.chdir(CUT_PLUGIN_PATH)
        p = subprocess.Popen([CUT_PLUGIN_EXE],
                             close_fds=True,
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        time.sleep(1)
        server_pids[CUT_PLUGIN_EXE] = p.pid
        os.chdir(SERVER_PATH)

        # Create a new acserver log file with a timestamp
        log_name = 'acServer.{}.log'.format(time.strftime("%m.%d.%Y.%H.%M.%S"))
        # Run the AC Server
        p = subprocess.Popen(['{} 1> {} 2>&1'.format(AC_SERVER_EXE, log_name)],
                             close_fds=True,
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        time.sleep(1)
        server_pids[AC_SERVER_EXE] = p.pid

        # Return True if server is running (may be misleading)
        return server_running()

    # Kills all processes with the name specified
    def kill_process(self, pid):
        p = subprocess.Popen(["cmd", "/C", "taskkill", "/PID", str(pid), "/f"], stdout=subprocess.PIPE)

    # Fragile if you rely on the PID file. Scorched earth, motherfucker.
    def kill_server(self):
        # Kill race server
        kill_process(server_pids[AC_SERVER_EXE])
        # Kill cut detector
        kill_process(server_pids[CUT_PLUGIN_EXE])
        # Kill ACRL_Plugin
        kill_process(server_pids[ACRL_PLUGIN_EXE])
        # Kill STracker
        kill_process(server_pids[STRACKER_EXE])

        # Return True if the server is stopped
        if not self.server_running():
            # TODO: upload logs here?
            return True
        return False

    def restart_server(self):
        if not self.kill_server():
            return False
        time.sleep(1)
        return self.start_server()

    # lol
    def instance_running(self):
        return True

    # Check to see if the ac server exe is in the list of running programs
    def server_running(self):
        server_is_running = False
        # Remember, this part is Windows only
        p1 = subprocess.Popen(["cmd", "/C", "tasklist"], stdout=subprocess.PIPE)
        output = p1.communicate()[0]
        # Get a list of process names and pids. Check if there is a match for the AC Server.
        for task_line in output.strip().split('\n'):
            split_line = task_line.split()
            if split_line[0] == AC_SERVER_EXE and split_line[1] == server_pids[AC_SERVER_EXE]:
                server_is_running = True

        return server_is_running

    # Returns new entry list as a string
    # TODO: Finish implementing at some point
    def current_entry_list(self, checkin_url):
        '''
        # Get the check-in list from google sheets. use gspread
        checkin_list = []  # list of username strings who checked in

        credentials = "google credentials"
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
        '''
        pass

    # Writes unsafely to the current config directory
    def write_current_entry_list(self, entry_list_string):
        p1 = subprocess.Popen(["cmd", "/C", "DIR /B", PRESETS_PATH], stdout=subprocess.PIPE)
        output = sorted(p1.communicate()[0])
        server_config_dir_name = output[0]
        with open(os.path.join(PRESETS_PATH, server_config_dir_name, ENTRY_LIST), 'w') as entry_list_ini:
            entry_list_ini.write(entry_list_string)



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


if __name__ == "__main__":
    # Get the args
    parser = argparse.ArgumentParser()
    parser.add_argument("-p",
                        "--port",
                        type=int,
                        help="Web server port for this server instance")
    args = parser.parse_args()

    # Important values to keep track of
    web_server_port = 8080
    if args.port:
        web_server_port = args.port

    # TODO: allow multiple servers to run
    # Our server
    acrl = Bottle()
    run(acrl, host='0.0.0.0', port=web_server_port)



"""
Start normally, with a flag to indicate if it should just check a normal location
otherwise, start and wait for some other mode of config

add methods to add server, remove server...
"""