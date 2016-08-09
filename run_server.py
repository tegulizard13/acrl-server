#/usr/bin/python
 
from boto.ec2 import connect_to_region
import logging
import time
import sys
import json
import requests


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
# TODO: set to INFO when done
ch.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
ch.setFormatter(console_formatter)
# Add our handlers to the root logger
root_logger.addHandler(fh)
root_logger.addHandler(ch)


class ACRLServer(object):
    def __init__(self, access_key_id, secret_access_key, region, instance_id):
        logging.info('Connecting to Amazon.')
        self.conn = connect_to_region(region,
                                      aws_access_key_id=access_key_id,
                                      aws_secret_access_key=secret_access_key)
        self.region = region
        self.instance_id = instance_id

    # TODO: Implement
    @property
    def instance_running(self):
        status = self.conn.get_all_instance_status(instance_ids=[self.instance_id])[0]
        logging.info("The instance state is: {}".format(status.state_name))
        return status.state_code == RUNNING

    # TODO: Implement
    @property
    def server_running(self):
        return False

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
    if not server.instance_running:
        # Start the instance
        server.start_instance()

    # The instance is running now, so we need to wait for the web service to become available
    logging.info("Trying to contact web service.")
    # TODO: make an http interface on the ec2 instance which can start the server
    # get the ip so we can contact the server
    sys.exit(0)


    # run commands over ssh, or using Fabric (or SSM for a windows instance)
    # fuck it, just make a tiny web server on the instance to launch everything from there
    
    # Get the user checkin list, and server config files from wherever they are stored
    # Put them in the correct location on the server

    # Run the server!
