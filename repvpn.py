#!/usr/bin/python
__author__ = 'IrekRomaniuk'
"""
Example:
[irekr@nms02 repvpn]$ pwd
/home/irekr/repvpn
[irekr@nms02 repvpn]$ python
Python 2.6.6 (r266:84292, Jan 22 2014, 09:37:14)
[GCC 4.4.7 20120313 (Red Hat 4.4.7-4)] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> from datetime import datetime
>>> import repvpn
>>> a=repvpn.list([])
>>> len(a)
>>>16384
>>> datetime.now()
>>> b=repvpn.ping(a)
>>> len(b)
>>>
>>> datetime.now()
"""

import os
import subprocess
from datetime import datetime


def list(a):
    """
    :param a: empty list
    :return: list of all rep vpn devices
    """
    a = []
    for i in xrange(192, 256):
        for j in xrange(0, 256):
            a.append('10.' + str(i) + '.' + str(j) + '.1')
    return a


def ping(a):
    """
    :param a: list of devices to ping
    :return b: list of active devices
    >>> ping(['10.29.1.1', '123.123.123.123', '123.123.123.123', '10.29.21.208'])
    ['10.29.1.1', '10.29.21.208']
    >>> ping(['10.29.1.1', '10.29.21.208'])
    ['10.29.1.1', '10.29.21.208']
    """
    b = []
    with open(os.devnull, "wb") as limbo:
        for ip in a:
            result = subprocess.Popen(["ping", "-c", "1", "-w", "1", ip], stdout=limbo, stderr=limbo).wait()
            if not result:
                b.append(ip)
    return b


if __name__ == '__main__':
    import doctest

    startTime = datetime.now()
    doctest.testmod()
    print "Program execution time:", datetime.now() - startTime

