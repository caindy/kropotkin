# Copyright Douglas Squirrel 2011
# This program comes with ABSOLUTELY NO WARRANTY. 
# It is free software, and you are welcome to redistribute it under certain conditions; see the GPLv3 license in the file LICENSE for details.

import json, messageboard, subprocess

def launch_code(code):
    p = subprocess.Popen(args="python", stdin=subprocess.PIPE)
    p.stdin.write(code)
    p.stdin.close()
    
def start_process(channel, serialised_process_data):
    try:
        print "Serialised process data: %s" % serialised_process_data
        process_data = json.loads(serialised_process_data)
        print "Process data: %s" % process_data
        name, key, code = process_data['name'], process_data['key'], process_data['code']

        launch_code(code)
    
        messageboard.post(channel=channel, key='process_started', body=name)

    except StandardError as e:
        print "Got exception %s" % str(e)

import time
time.sleep(1)
channel = messageboard.get_connection()
messageboard.start_consuming(channel=channel, name='start_process', key='start_process', callback=start_process)
