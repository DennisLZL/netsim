__author__ = 'dennis'

import numpy as np
from scipy.stats import rv_discrete
import datetime as dt

# protocol samples
protocols = ['iec104', 'modbus', 'dnp3', 'opcda', 'profinetio', 'TIAS_TETRA', 's7', 'mms', 'udp', 'ftp', 'tcp']
protocol_sample = dict()
for p in protocols:
    with open('config/'+p+'sample', 'r') as f:
        protocol_sample[p] = f.read().splitlines()


# network node
class Node:
    nodeCnt = 0  # total number of nodes

    def __init__(self, ip, mac, proset, type):
        Node.nodeCnt += 1
        self.id = Node.nodeCnt
        self.ip = ip
        self.mac = mac
        self.proset = proset  # dict {'protocol': weight}
        self.type = type

    def commMsg(self, dest, time):
        """
        messages between two nodes
        :param dest: node receiving the message
        :param time: time generating the message
        :return: flow data
        """
        prols = list(set(self.proset.keys()).intersection(set(dest.proset.keys())))
        wt = np.array([self.proset[x] for x in prols]) + np.array([dest.proset[x] for x in prols])
        wt /= float(wt.sum())

        protocol = prols[rv_discrete(values=(range(len(prols)), wt)).rvs(size=1)]
        dataflow = []

        msg = protocol_sample[protocol][np.random.randint(len(protocol_sample[protocol]))]
        dataflow.append(', '.join([self.ip, dest.ip, msg, time, '1', self.mac, dest.mac]))
        dataflow.append(', '.join([dest.ip, self.ip, msg, time, '1', dest.mac, self.mac]))

        return dataflow

# network
class Network:
    


def ipList(n):
    ip_range = []
    ip = [192, 168, 0, 0]
    for k in range(n + 1):
        ip[3] += 1
        for i in (3, 2, 1):
            if ip[i] == 255:
                ip[i] = 0
                ip[i - 1] += 1
        ip_range.append('.'.join(map(str, ip)))
    return ip_range

def macList(n):
    mac_list = []
    for i in range(n):
        mac = [0x52, 0x54, 0x00, np.random.randint(0x00, 0x7f), np.random.randint(0x00, 0xff), np.random.randint(0x00, 0xff)]
        mac_list.append(''.join(map(lambda x: "%02x" % x, mac)))
    return mac_list

if __name__ == '__main__':
    ips = ipList(2)
    macs = macList(2)
    node1 = Node(ips[0], macs[0], {'tcp': 1., 'iec104': 1., 'modbus': 1.}, 'workStation')
    node2 = Node(ips[1], macs[1], {'tcp': 1., 'modbus': 1.}, 'PLC')

    t = dt.datetime.now().strftime('%m/%d/%Y-%H:%M:%S.%f')

    data = node1.commMsg(node2, t)
    for m in data:
        print m