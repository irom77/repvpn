#!/usr/bin/python
__author__ = 'http://blog.boa.nu/2012/10/python-threading-example-creating-pingerpy.html'
"""
Example of rep.py usage:

[irekr@nms02 repvpn]$ [irekr@nms02 repvpn]$ python rep.py
Address AC107D66 Time 2015-03-22 17:48:26.775246: total of 908 addresses
                 Time 2015-03-22 17:48:32.741735: total of 890 update

Example of MongoDB use:

[irekr@nms02 repvpn]$mongo
MongoDB shell version: 2.6.8
connecting to: test
> use devices
switched to db devices
> db
devices
> db.repvpn.stats().count
"""
import subprocess
import threading
import sys
from datetime import datetime
import pymongo


class Targets(object):
    """
    Example:
    >>> from rep import Targets
    >>> targets=Targets()
    >>> ip=targets.list1s()
    >>> len(ip)
    16384
    >>> print ip[0],ip[-1]
    10.192.0.1 10.255.255.1
    >>> targets.sample() # pick 10 addresses
    """
    def list1s(self):
        """
        :return: list of all rep vpn devices
        """
        return ["10." + str(x) + "." + str(y) + ".1" for x in range(192, 256) for y in range(0, 256)]

    def sample(self):
        """
        :return: list 10 random addresses
        """
        import random
        return random.sample(self.list1s(), 10)

    def fromdb(self):  # ,time
        db = pymongo.Connection()["devices"]
        vpn = db["repvpn"]
        return [str(ip["address"]) for ip in vpn.find()]  # print vpn.count() # if ip["last"] > time

    def findmyip(self):
        import socket
        import binascii
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('google.com', 0))
        return binascii.hexlify(socket.inet_aton(s.getsockname()[0])).upper()


class Rep(object):
    """
    Class Rep based on http://blog.boa.nu
    Example:
    >>> from rep import Targets, Rep
    >>> targets=Targets()
    >>> ping=Rep()
    >>> ping.thread_count = 50
    >>> ping.updated = 0
    >>> ping.source=targets.findmyip()
    >>> ping.hosts = targets.fromdb()
    >>> len(ping.hosts)
    908
    >>> ping.start()
    >>> print ping.updated
    892
    """
    hosts = []  # List of all hosts/ips in our input queue
    # Connect to db
    db = pymongo.Connection()["devices"]
    vpn = db["repvpn"]
    vpn.ensure_index("address", unique=True)
    thread_count = 5  # used if __name__ != '__main__'
    source = '' # source ip address of ping/ssh
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
            if self.ping(ip):
                self.vpn.update({"address": ip}, {"$set": {self.source: datetime.now()}})
                self.updated += 1

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
    ping = Rep()
    ping.thread_count = 50  # default
    ping.updated = 0
    dtStrt = datetime.now()  # .isoformat()
    #dtDate = datetime.strptime("03/03/2015", "%m/%d/%Y")  # .isoformat()
    targets = Targets()
    ping.source = targets.findmyip()
    if len(sys.argv) >= 2:
        if sys.argv[1] == 'tst':
            ping.hosts = targets.sample()
            ping.thread_count = 10
        elif sys.argv[1] == 'all':
            ping.hosts = targets.list1s()
            ping.thread_count = 100
    else:
        ping.hosts = targets.fromdb()
    print "Address %s Time %s: total of %s addresses" % (ping.source, dtStrt, len(ping.hosts))
    ping.start()
    print "                 Time %s: total of %s updated" % (datetime.now(), ping.updated)


