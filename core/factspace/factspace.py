#!/usr/bin/python
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from glob import glob
from httplib2 import Http
from json import dumps, load
from kropotkin import store_fact
from multiprocessing import Process
from os import rename
from os.path import join
from tempfile import mkdtemp
from time import time
from urlparse import urlparse, parse_qsl

class base_factspace_handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urlparse(self.path)
        url_path = parsed_url.path
        query_params = dict(parse_qsl(parsed_url.query))

        if url_path == '/':
            self.give_response(200, '%s Factspace\n' % self.server_name)
        else:
            fact_type = url_path.split('/')[1]
            facts = self.fetch_facts(fact_type, query_params)
            self.give_response(200, dumps(facts), 'application/json')

    def fetch_facts(self, fact_type, query_params):
        query_params = query_params.copy()
        stamp, result = self.extract_kropotkin_criteria(query_params)
        query_params.pop('kropotkin_criteria', None)

        fact_files = glob(join(self.facts_dir, fact_type + ".*"))
        fact_files.sort(key=lambda f: int(f.split('.')[1]))

        if stamp:
            root = stamp.split('.')[0]
            fact_files = [f for f in fact_files if not root in f]

        query_params_set = set(query_params.items())
        def query_filter(f):
            return query_params_set < set(self.load_fact(f).viewitems())
        fact_files = [f for f in fact_files if query_filter(f)]

        if result == 'oldest':
            fact_files = fact_files[0:1]
        elif result == 'newest':
            fact_files = fact_files[-1:]

        if stamp:
            for i, f in enumerate(fact_files):
                new_name = '.'.join([f, stamp])
                rename(f, new_name)
                fact_files[i] = new_name
        
        return [self.load_fact(f) for f in fact_files]

    def do_POST(self):
        fact_type = (urlparse(self.path).path)[1:]
        length = int(self.headers.getheader('Content-Length'))
        content = self.rfile.read(length)

        if fact_type and content:
            self.save_fact(fact_type, content)
            self.give_response(200, '')
        else:
            self.give_response(400, '')

    def log_message(self, format, *args):
        return

    def give_response(self, resp_code, text, mime_type='text/plain'):
        self.send_response(resp_code)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(text))
        self.send_header('Content-Type', mime_type + '; charset=utf-8')
        self.end_headers()
        if text:
            self.wfile.write(text)

    def extract_kropotkin_criteria(self, query_params):
        stamp = False
        result = 'all'
        try:
            criteria_str = query_params['kropotkin_criteria']
            criteria_str = criteria_str.replace('-', '=').replace(',', '&')
            criteria = dict(parse_qsl(criteria_str))
            try:
                stamp  = criteria['stamp']
            except KeyError:
                pass
            try:
                result = criteria['result']
            except KeyError:
                pass
        except KeyError:
            pass
        return stamp, result

    def save_fact(self, fact_type, content):
        tstamp = int(time())
        name = '.'.join([fact_type, str(tstamp), str(hash(content)), 'fact'])
        with open(join(self.facts_dir, name), 'w') as fact_file:
            fact_file.write(content)

    def load_fact(self, fact_filename):
        with open(fact_filename, 'r') as fact_file:
            return load(fact_file)

def start_factspace(name, port, kropotkin_url):
    print "Starting factspace %s on port %d; kropotkin at %s"\
        % (name, port, kropotkin_url)

    class factspace_handler(base_factspace_handler):
        facts_dir = mkdtemp()
        server_name = name
    print "Storing facts in %s" % factspace_handler.facts_dir

    server = HTTPServer(('', port), factspace_handler)
    process = Process(target=server.serve_forever)
    process.start()

    content = dumps({'name':name, 'port':port})
    store_fact(kropotkin_url, 'service-started', content)

if __name__=="__main__":
    print "Running factspace component"