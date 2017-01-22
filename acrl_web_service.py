# TODO: Fix logging so that it works correctly, it isn't logging now...
# TODO: Links to race log files for after the race.
# pip install bottle, requests
"""
Bottle server with api methods for starting everything
"""
import argparse
import logging
import os
import shutil
import multiprocessing
import subprocess
import time

import bottle
from bottle import request, template, view


# Configuration paths and files
SERVER_PATH = 'C:\Users\Administrator\Desktop'
PLUGIN_DIR = 'Plugins'
CONFIG_DIR = 'cfg'
STAGING_DIR = os.path.join(CONFIG_DIR, 'staging')

REGION_NA = 'NA'
REGION_EU = 'EU'

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


class ServerApp(object):
    def __init__(self, base_dir=None):
        """
        Base class for applications running on the host device.

        :param base_dir: Folder name EU1, EU2, etc... NA1, NA2, etc... containing acserver.exe

        :var base_dir: Absolute path to the server base directory
        :var pid: process Id for the process if running
        :var directory: Path to the application executable directory relative to _base_path
        :var executable: Executable file name
        :var launcher: Windows shell script in _base_path which can be used to run the app
        """

        # TODO: determine the next dir automagically
        if not base_dir:
            # list the dirs on the desktop to see how many servers there are
            # make a new folder via a copy or something?
            raise Exception('need a base dir for now')

        self.base_path = os.path.join(SERVER_PATH, base_dir)
        self.pid = None
        self.directory = None
        self.executable = None
        self.launcher = None

    @property
    def running(self):
        application_running = False
        p = subprocess.Popen(["cmd", "/C", "tasklist"], stdout=subprocess.PIPE)
        output = p.communicate()[0]

        # Get a list of process names and pids. Check if there is a match for the application.
        for task_line in output.strip().split('\n'):
            split_line = task_line.split()
            if split_line[0] == self.executable and split_line[1] == self.pid:
                application_running = True

        return application_running

    def run(self):
        """
        Runs the application executable directly with args. Gets the PID.
        """
        pass

    def run_launcher(self):
        """
        Runs the application using a windows shell script. No application PID available.
        :return: Boolean True to indicate success
        """
        process_running = False
        if self.launcher:
            os.chdir(self.base_path)
            p = subprocess.Popen([self.launcher],
                                 close_fds=True,
                                 creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
            time.sleep(1)
            self.pid = p.pid
            process_running = True
        return process_running

    def kill(self):
        p = subprocess.Popen(["cmd", "/C", "taskkill", "/PID", str(self.pid), "/f"], stdout=subprocess.PIPE)


class ACServer(ServerApp):
    def __init__(self, base_dir):
        super(ACServer, self).__init__(base_dir)
        self.executable = 'acServer.exe'
        self.launcher = 'Start - Server.bat'

    def run(self):
        os.chdir(self.base_path)

        # get a timestamp for the log files
        log_suffix = '{}.log'.format(time.strftime("%m.%d.%Y.%H.%M.%S"))
        log_output = 'logs/session/output-{}'.format(log_suffix)
        log_error =  'logs/error/error-{}'.format(log_suffix)

        # Run the AC Server
        ac_run_str = '{} > {} 2> {}'.format(self.executable, log_output, log_error)
        p = subprocess.Popen([ac_run_str],
                             close_fds=True,
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        time.sleep(1)
        self.pid = p.pid


class Stracker(ServerApp):
    def __init__(self, base_dir, level=1):
        super(Stracker, self).__init__(base_dir)
        self.directory = 'stracker'
        self.executable = 'stracker.exe'
        self.level = level

    @property
    def launcher(self):
        return 'Start - Plugin - Stracker - L{}.cmd'.format(self.level)

    def run(self):
        run_dir = os.path.join(self.base_path, PLUGIN_DIR, self.directory)
        os.chdir(run_dir)
        # Run the Stracker Plugin
        p = subprocess.Popen([self.executable, '--stracker_ini', 'stracker-forwarded-l{}.ini'.format(self.level)],
                             close_fds=True,
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        time.sleep(1)
        self.pid = p.pid


class RollingStartPlugin(ServerApp):
    def __init__(self, base_dir):
        super(RollingStartPlugin, self).__init__(base_dir)
        self.directory = 'rollingstart'
        self.executable = 'RollingStartPlugin.exe'
        self.launcher = 'Start - Plugin - Rolling L2.bat'

    def run(self):
        run_dir = os.path.join(self.base_path, PLUGIN_DIR, self.directory)
        os.chdir(run_dir)

        # Run the Rolling Start Plugin
        p = subprocess.Popen([self.executable],
                             close_fds=True,
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        time.sleep(1)
        self.pid = p.pid


class CutPlugin(ServerApp):
    def __init__(self, base_dir):
        super(CutPlugin, self).__init__(base_dir)
        self.directory = 'cut'
        self.executable = 'ACCutDetectorPlugin.exe'
        self.launcher = 'Start - Plugin - Cut - L1.bat'

    def run(self):
        run_dir = os.path.join(self.base_path, PLUGIN_DIR, self.directory)
        os.chdir(run_dir)

        # Run the Cut Plugin
        p = subprocess.Popen([self.executable],
                             close_fds=True,
                             creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)
        time.sleep(1)
        self.pid = p.pid


class ACRLServer(object):
    def __init__(self, base_dir, http_port, plugins=None):
        """
        ACRL Server instance representing a single game server and its plugins

        :param base_dir: Folder name EU1, EU2, etc... NA1, NA2, etc... containing acserver.exe
        :param http_port: Port the server should use for http
        :param plugins: List of plugin class types in the order they should be started.

        :var apps: List of application instances, once start_server() has been called
        :var _plugins: list of plugin class types in the order they should be started
        :var _bottle_app: bottle app instance for this game server
        :var _http_process: Python bottle app run process for this game server.
        """

        self.base_dir = base_dir
        self.http_port = http_port
        self.apps = []
        self._plugins = plugins if plugins else []

        self._bottle_app = None
        self._http_process = None

    # Start the server processes
    def start_server(self):
        for index, Plugin in enumerate(self._plugins):
            # Create an instance of the plugin class type in the list. Keep track of it.
            self.apps.append(Plugin(base_dir=self.base_dir))

            # Stracker needs an additional arg, so if this plugin is Stracker than set it.
            if type(self.apps[-1]) is Stracker:
                self.apps[-1].level = index

            self.apps[-1].run()
        time.sleep(1)

        # We will kill processes in order later, so add the game server to the start of the apps list
        self.apps = [ACServer(base_dir=self.base_dir)] + self.apps
        self.apps[0].run()

        # Return True if server is running
        return self.server_running()

    # Attempt to kill all server applications by PID
    def kill_server(self):
        for app in self.apps:
            app.kill()
        time.sleep(1)

        # Return True if the server is stopped
        return not self.server_running()

    def restart_server(self):
        if not self.kill_server():
            return False
        time.sleep(1)
        return self.start_server()

    def server_running(self):
        """
        Checks each process for this server and ANDs the statuses
        :return: Boolean True if all required applications have PIDs in tasklist output
        """
        server_is_running = True

        for app in self.apps:
            server_is_running = server_is_running and app.running

        all_running = len(self.apps) == len(self._plugins) + 1
        server_is_running = server_is_running and all_running

        return server_is_running

    """
    ------------------------------------------------------------------------
    Ideally I would decorate these methods. These are page routes and setup.
    ------------------------------------------------------------------------
    """

    def run_http(self):
        self._bottle_app = bottle.Bottle()
        self.setup_routes()
        self._http_process = multiprocessing.Process(target=bottle.run,
                                                     args=(self._bottle_app, ),
                                                     kwargs={'port': self.http_port})
        self._http_process.start()

    def kill_http(self):
        self._http_process.terminate()

    def setup_routes(self):
        """
        Setup the page routes for the methods below
        """
        self._bottle_app.route('/', [GET], self.status)
        self._bottle_app.route('/about', [GET], self.home)
        self._bottle_app.route('/control', [POST], self.control_server)
        self._bottle_app.route('/upload', [POST], self.upload_configs)

    # Check the status and generate an in-depth status page, with links to do things
    @view('status')
    def status(self):
        return dict(server_running=self.server_running())

    def home(self):
        return template('about')

    def control_server(self):
        action = request.forms.get('action')
        if action == START:
            self.start_server()
        elif action == STOP:
            self.kill_server()
        elif action == RESTART:
            self.restart_server()
        time.sleep(1)
        return template('redirect_home')

    # TODO: add better exception handling
    def upload_configs(self):
        entry_list_generated = False
        server_cfg_written = False
        try:
            staging_path = os.path.join(SERVER_PATH, self.base_dir, STAGING_DIR)
            if not os.path.exists(staging_path):
                os.makedirs(staging_path)

            server_cfg = request.files.get('server_cfg')
            entry_list = request.files.get('entry_list')

            # Attempt to write the uploaded server config to the staging directory
            server_config_path = os.path.join(staging_path, server_cfg.filename)
            server_cfg.save(server_config_path, overwrite=True)
            server_cfg_written = True

            # Attempt to write the uploaded entry list to the staging directory
            entry_list_path = os.path.join(staging_path, entry_list.filename)
            entry_list.save(entry_list_path, overwrite=True)
            entry_list_generated = True

            # Copy the new configs to the active config directory
            shutil.copy(server_config_path,
                        os.path.join(SERVER_PATH, self.base_dir, CONFIG_DIR, SERVER_CFG))
            shutil.copy(entry_list_path,
                        os.path.join(SERVER_PATH, self.base_dir, CONFIG_DIR, ENTRY_LIST))
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

    plugins1 = [CutPlugin, RollingStartPlugin, Stracker]
    plugins2 = [CutPlugin, Stracker]

    # EXAMPLE of how to start up multiple configured http server instances
    server1 = ACRLServer(base_dir='EU1', http_port=web_server_port, plugins=plugins1)
    server2 = ACRLServer(base_dir='EU2', http_port=web_server_port+2, plugins=plugins2)
    server1.run_http()
    server2.run_http()

    time.sleep(20)

    server1.kill_http()
    server2.kill_http()
