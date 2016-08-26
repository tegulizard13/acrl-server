#/usr/bin/python
 
from boto.ec2 import connect_to_region
from httplib import OK
import logging
import time
import sys
import json
import requests
import webbrowser

RUNNING = 16
TIMEOUT = 300


# Set up logging, so if something goes wrong there is a file to send to get help.
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
# Log to file
fh = logging.FileHandler('ACRL.log')
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


class ACRLServer(object):
    def __init__(self, access_key_id, secret_access_key, region, instance_id, ip=None):
        logging.info('Connecting to Amazon.')
        self.conn = connect_to_region(region,
                                      aws_access_key_id=access_key_id,
                                      aws_secret_access_key=secret_access_key)
        self.region = region
        self.instance_id = instance_id
        self._ip = ip

    # Checks the instance state according to Amazon
    @property
    def instance_running(self):
        status = self.conn.get_all_instance_status(instance_ids=[self.instance_id])[0]
        logging.info("The instance state is: {}".format(status.state_name))
        return status.state_code == RUNNING

    # Will attempt to get/set the ip of the instance, returns None if unavailable
    # TODO: this will break if the instance dies before this script finishes
    @property
    def ip(self):
        if not self._ip:
            if self.instance_running:
                instance = self.conn.get_all_instances(instance_ids=[self.instance_id])[0]
                self._ip = str(instance.instances[0].ip_address)
        return self._ip

    # Blocks, could spin up a thread if you wanted
    def start_instance(self):
        start_time = time.time()
        logging.info("Starting Amazon EC2 instance {}.".format(self.instance_id))
        self.conn.run_instances(self.instance_id, 0, 1)
        time.sleep(10)
        while not self.instance_running:
            sys.exit(0) #Do this for now to be non-destructive
            logging.info("Waited for instance to start for {} seconds.".format(time.time()-start_time))
            if time.time()-start_time >= TIMEOUT:
                raise Exception('Timed out waiting for instance to start')
            time.sleep(5)

if __name__ == "__main__":
    # Read in the AWS keys and other private info
    acrl_info = None
    with open("acrl_info.json", "r") as acrl_info_json:
        acrl_info = json.load(acrl_info_json)

    # Set up an authenticated connection with Amazon
    server = ACRLServer(access_key_id=acrl_info["access_key_id"],
                        secret_access_key=acrl_info["secret_access_key"],
                        region=acrl_info["region"],
                        instance_id=acrl_info["instance_id"])

    logging.info("Checking if the instance is running.")
    ip = server.ip
    if not ip:
        # Start the instance
        #server.start_instance()
        pass

    # The instance is running now, so we need to wait for the web service to become available
    logging.info("Trying to contact web service.")
    start_time = time.time()

    # Needs a method caller with a proper timeout
    while True:
        if time.time() - start_time >= TIMEOUT:
            raise Exception('Timed out waiting for web service to be available')
        response = requests.head("http://{}:8080/".format(ip))
        if response.status_code == OK:
            break
        time.sleep(5)

    logging.info("The http server is running at http://{}:8080/".format(ip))
    logging.info("Opening the web page")
    webbrowser.open("http://{}:8080/".format(ip))
    sys.exit(0)