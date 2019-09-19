#!/usr/bin/env python3

import base64
import hashlib
import json
import os
import requests
import signal
import sys
import threading
import time
import uuid

from datetime import timedelta


CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 5))
ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://es:9200')
LOGSTASH_URL = os.getenv('LOGSTASH_URL', 'http://ls:8080')
OLD_CHECK = '/tmp/old_check'


class ProcessKilled(Exception):
    pass


def signal_handler(signum, frame):
    raise ProcessKilled


class Job(threading.Thread):
    def __init__(self, interval, execute, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs

    def stop(self):
        self.stopped.set()
        self.join()

    def run(self):
        while not self.stopped.wait(self.interval.total_seconds()):
            self.execute(*self.args, **self.kwargs)


def task():
    # check if the old secret is on Elasticsearch
    if os.path.isfile(OLD_CHECK):
        
        # get the old secret from local storage
        with open(OLD_CHECK, 'r') as oc_file:
            old_check = oc_file.readlines()[0]
            oc_file.close()

        # compute the fingerprint
        dgst = hashlib.sha256(old_check.encode()).digest()
        fingerprint = base64.b64encode(dgst).decode()

        try:
            r = requests.get('%s/elkhealth/doc/check' % ELASTICSEARCH_URL)
            doc = r.json()['_source']

            print('Checking %s on Elasticseach' % old_check)

            for k in ['message', 'fingerprint', 'tags']:
                if k not in doc:
                    #
                    # send someone some notification
                    #
                    print('##')
                    print('##')
                    print('## Houston, we have a problem!!!')
                    print('## The "%s" key is missing' % k)
                    print('##')
                    print('##')

                    return

            if (    doc['message'] == old_check
                and doc['fingerprint'] == fingerprint
                and set(doc['tags']) >= set(['elkhealth_input', 'elkhealth_filter'])
               ):
                print('The %s check has been found' % old_check)
            else:
                #
                # send someone some notification
                #
                print('##')
                print('##')
                print('## Houston, we have a problem!!!')
                print('## Obtained data are different from the computed one')
                print('##')
                print('##')

                return
        except:
            print('Elasticsearch could be not reachable')

    # compute a new check and push on the ELK pipeline
    new_check = str(uuid.uuid4())
    data = {'message': new_check, 'type': 'elkhealth'}

    try:
        r = requests.put(LOGSTASH_URL, json=data)
        print('Pushing %s on the ELK pipeline' % new_check)

        while r.text != 'ok':
            time.sleep(5)
            r = requests(LOGSTASH_URL, json=data)
            print('Re-pushing %s on the ELK pipeline' % new_check)

        # save the check for future check
        with open(OLD_CHECK, 'w') as oc_file:
            oc_file.write(new_check)
            oc_file.close()
    except:
        print('Logstash could be not reachable')


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    job = Job(interval=timedelta(seconds=CHECK_INTERVAL), execute=task)
    job.start()

    while True:
        try:
            time.sleep(1)
        except ProcessKilled:
            job.stop()
            break
