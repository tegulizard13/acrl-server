'''
Bottle server with api methods for starting everything
'''
from bottle import Bottle, run
import subprocess

# HTTP Verbs
POST = "POST"
PUT = "PUT"
GET = "GET"
HEAD = "HEAD"
DELETE = "DELETE"

#
# Our server
acrl = Bottle()


@acrl.route('/status', method=GET)
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


# lol
def instance_running():
    return True


# Check to see if the server exe is in the list of running programs
def server_running():
    server_is_running = False

    p1 = subprocess.Popen(["cmd", "/C", "tasklist"], stdout=subprocess.PIPE)
    output = p1.communicate()[0]
    # Get a list of process names
    programs_running = [name.split()[0] for name in output.strip().split('\n')]
    if "acServer.exe" in programs_running:
        server_is_running = True
    return server_is_running


if __name__ == "__main__":
    run(acrl, host='127.0.0.1', port=8080)