#!/usr/bin/python
__author__ = 'http://blog.boa.nu/2012/10/python-threading-example-creating-pingerpy.html'
"""
Example of initial pinger class:
[irekr@nms02 repvpn]$ pwd
/home/irekr/repvpn
[irekr@nms02 repvpn]$ python pinger.py
{'dead': ['*not able to ping!*', 'nonexisting', '10.0.0.0', '10.0.0.100', '10.0.0.4', '10.0.0.3',
 '10.0.0.255', '10.0.0.2'], 'alive': ['127.0.1.2', '8.8.8.8', 'google.com', 'github.com', '10.29.1.1']}
[irekr@nms02 repvpn]$ time python pinger.py 50
Completed with thread_count 50
alive: 995 dead: 15389

real    5m13.869s
user    0m24.066s
sys     1m48.781s

[irekr@nms02 repvpn]$ time python pinger.py 100
Completed with thread_count 100
alive: 996 dead: 15388

real    2m41.318s
user    0m33.678s
sys     3m8.158s
[irekr@nms02 repvpn]$ python
Python 2.6.6 (r266:84292, Jan 22 2014, 09:37:14)
[GCC 4.4.7 20120313 (Red Hat 4.4.7-4)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from pinger import Pinger
>>> import repvpn
>>> ping=Pinger()
>>> ping.thread_count=50
>>> ping.hosts=repvpn.list([])
>>> len(ping.hosts)
16384
>>> ping.start()
>>> len(ping.status['alive'])
995
>>> len(ping.status['dead'])
15389
Example of recording in MongoDB
[irekr@nms02 repvpn]$mongo
> use devices
switched to db devices
> db.repvpn.find()
{ "_id" : ObjectId("54f4c80a05000e14a0d41b34"), "last" : ISODate("2015-03-02T15:28:58.866Z"), "address" : "127.0.1.2" }
{ "_id" : ObjectId("54f4c80a05000e14a0d41b35"), "last" : ISODate("2015-03-02T15:28:58.882Z"), "address" : "8.8.8.8" }
{ "_id" : ObjectId("54f4c80a05000e14a0d41b36"), "last" : ISODate("2015-03-02T15:28:58.903Z"), "address" : "google.com" }
{ "_id" : ObjectId("54f4c80a05000e14a0d41b37"), "last" : ISODate("2015-03-02T15:28:58.917Z"), "address" : "github.com" }
{ "_id" : ObjectId("54f4c96305000e23c998e847"), "last" : ISODate("2015-03-02T15:34:43.701Z"), "address" : "yahoo.com" }
>>> from pinger import Pinger
>>> print Pinger.hosts
[]
>>> import repvpn
>>> Pinger.hosts = repvpn.list([])
>>> len(Pinger.hosts)
16384
"""
import subprocess
import threading
import sys
from datetime import datetime
import pymongo


class Pinger(object):
    """
    Class Pinger based on http://blog.boa.nu
    status used in the initial class version, here replaced by recording in MongoDB
    status = {'alive': [], 'dead': []}  # Populated while we are running
    """
    hosts = []  # List of all hosts/ips in our input queue

    # Connect to db
    db = pymongo.Connection()["devices"]
    vpn = db["repvpn"]
    vpn.ensure_index("address", unique=True)

    # How many ping process at the time.
    thread_count = 4

    # Lock object to keep track the threads in loops, where it can potentially be race conditions.
    lock = threading.Lock()

    def ping(self, ip):
        # Use the system ping command with count of 1 and wait time of 1.
        ret = subprocess.call(['ping', '-c', '1', '-W', '1', ip],
                              stdout=open('/dev/null', 'w'), stderr=open('/dev/null', 'w'))

        return ret == 0  # Return True if our ping command succeeds

    def pop_queue(self):
        ip = None

        self.lock.acquire()  # Grab or wait+grab the lock.

        if self.hosts:
            ip = self.hosts.pop()

        self.lock.release()  # Release the lock, so another thread could grab it.

        return ip

    def dequeue(self):
        while True:
            ip = self.pop_queue()

            if not ip:
                return None
            # status used in the initial class version
            # result = 'alive' if self.ping(ip) else 'dead'
            if self.ping(ip):
                self.vpn.insert({"address": ip, 'last': datetime.now()})
            else:
                self.vpn.remove({"address": ip})
            # self.status[result].append(ip)

    def start(self):
        threads = []

        for i in range(self.thread_count):
            # Create self.thread_count number of threads that together will
            # cooperate removing every ip in the list. Each thread will do the
            # job as fast as it can.
            t = threading.Thread(target=self.dequeue)
            t.start()
            threads.append(t)

        # Wait until all the threads are done. .join() is blocking.
        [t.join() for t in threads]
        # status used in the initial class version
        # return self.status


if __name__ == '__main__':
    import repvpn

    ping = Pinger()
    ping.thread_count = 10  # default


    try:
        sys.argv[1], sys.argv[2]
    except IndexError:
        print "usage is...\npython pinger.py thread_count xxx"
        print "xxx=add - add new devices to db (full scan)"
        print "xxx=del - remove not responding devices"
        print "xxx=tst - test with list"
        print "xxx='' - by default work with current db"
        sys.exit(1)
    else:
        ping.thread_count = int(sys.argv[1])
    if sys.argv[2] == 'tst':
        ping.hosts = [
        '10.0.0.1', '10.0.0.2', '10.0.0.3', '10.0.0.4', '10.0.0.0', '10.0.0.255', '10.0.0.100',
        'google.com', 'github.com', 'nonexisting', '127.0.1.2', '*not able to ping!*', '8.8.8.8',
        'yahoo.com', '123.123.123.123'
        ]
    elif sys.argv[2] == 'add':
            ping.hosts = repvpn.list([])
    else:
        db = pymongo.Connection()["devices"]
        vpn = db["repvpn"]
        for ip in vpn.find():
            ping.hosts.append(str(ip["address"]))
    print "len of ping.hosts %s and thread-count is %s" % (len(ping.hosts),ping.thread_count)
    #print ping.hosts
    # sys.exit()
    ping.start()
    # status used in original class version, replaced by mongodb
    # print "Completed with thread_count %s\nalive: %s dead: %s" % (ping.thread_count, len(ping.status['alive']),
                                                                  #len(ping.status['dead']))
