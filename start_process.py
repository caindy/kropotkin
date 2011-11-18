import messageboard, subprocess, time

def start_process(serialised_process_data):
    try:
        process_data = eval(serialised_process_data)
        verb, code = process_data['verb'], process_data['code']

        print "Starting process"
        print "Process code:\n%s" % code

        p = subprocess.Popen(args="python", stdin=subprocess.PIPE)
        p.stdin.write(code)
        p.stdin.close()
    
        print "Process started"

    except StandardError as e:
        print "Got exception %s" % str(e)

def run_tests():
    return True

messageboard.start_consuming(verb='start_process', callback=start_process, run_tests=run_tests)
