acrl-server
Automation for running an Assetto Corsa server on Amazon Web Services

# Prerequisites
Python and pip need to be installed on both clients and instances, and then packages installed with pip:
pip install requests boto bottle gspread

# On the instances
I also cloned the repo to users/ACRacingLeage/acrl-server
Make sure acrl_web_service.py starts at boot. I had to do this as admin to get it to stick

