#/usr/bin/python
 
import boto.ec2
import logging
import time
import sys
import requests

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
ch.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(levelname)s: %(message)s')
ch.setFormatter(console_formatter)
# Add our handlers to the root logger
root_logger.addHandler(fh)
root_logger.addHandler(ch)


class ACRLServer
if __name__ == "__main__":
    instance_id = 'id'

    logging.info('Connecting to Amazon.')
    #conn = boto.ec2.connect_to_region("us-west-2")

    sys.exit(0)
    logging.info('Running ACRL EC2 Instance.')
    reservation = conn.run_instances(
        instance_id,
        key_name='key_pair_name',
        instance_type='t1.micro',
        security_groups=['user_security_groups']
    )
    instance = reservation.instances[0]

    # wait for the instance to become active
    logging.info('Waiting for the instance to become active...')
    while instance.state != 'running':
        #print '...instance is %s' % instance.state
        logging.info
        time.sleep(5)
        instance.update()
    logging.info('It Lives!')

    # Get the public ip of the instance
    ip = instance['PublicIpAddress']

    # run commands over ssh, or using Fabric (or SSM for a windows instance)
    
    # Get the user checkin list, and server config files from wherever they are stored
    # Put them in the correct location on the server

    # Run the server!
