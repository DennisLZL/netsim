__author__ = 'dennis'

import numpy as np
from scipy.stats import rv_discrete
import datetime as dt
import json

# protocol samples
protocols = ['iec104', 'modbus', 'dnp3', 'opcda', 'profinetio', 'TIAS_TETRA', 's7', 'mms', 'udp', 'ftp', 'tcp']
protocol_sample = dict()
for p in protocols:
    with open('config/' + p + 'sample', 'r') as f:
        protocol_sample[p] = f.read().splitlines()


# network node
class Node:
    nodeCnt = 0  # total number of nodes

    def __init__(self, ip, mac, type):
        """
        :param ip: ip address
        :param mac: mac address
        :param type: device type, e.g. 'ws', 'plc', 'server'
        :return: Node object
        """
        Node.nodeCnt += 1
        self.id = Node.nodeCnt
        self.ip = ip
        self.mac = mac
        self.type = type

    def nodeComm(self, dest, protocol, time):
        """
        :param dest: node to communicate with
        :param protocol: protocol to use
        :param time: time
        :return: a list of data flow between two nodes
        """
        data_flow = []
        msg = protocol_sample[protocol][np.random.randint(len(protocol_sample[protocol]))]
        data_flow.append(', '.join([self.ip, dest.ip, msg, time, '1', self.mac, dest.mac]))
        data_flow.append(', '.join([dest.ip, self.ip, msg, time, '1', dest.mac, self.mac]))
        return data_flow


# connection
class Connection:
    def __init__(self, zoneA, zoneB, prodict, freq):
        """
        :param zoneA: a list of Node objects
        :param zoneB: a list of Node objects
        :param prodict: protocol weight dict, e.g. {'modbus': 1}
        :param freq: message frequency
        :return: connection object
        """
        self.zoneA = zoneA
        self.zoneB = zoneB
        self.prodict = prodict
        self.freq = freq

    def connComm(self, time):
        """
        :param time: time
        :return: a list of data flow between two zones
        """
        prols = self.prodict.keys()
        wt = np.array(self.prodict.values()).astype(float)
        wt /= wt.sum()
        protocol = prols[rv_discrete(values=(range(len(prols)), wt)).rvs(size=1)]

        i = np.random.randint(len(self.zoneA))
        j = np.random.randint(len(self.zoneB))
        return self.zoneA[i].nodeComm(self.zoneB[j], protocol, time)

    def toDict(self):
        """
        :return: convert object to dict
        """
        d = vars(self)
        d['zoneA'] = [vars(x) for x in self.zoneA]
        d['zoneB'] = [vars(x) for x in self.zoneB]
        return d

class Network:

    def __init__(self, n, typeList, rules):
        """
        :param n: number of devices
        :param typeList: a list of device type
        :param rules: e.g. [{'zoneA':[1,2,3], 'zoneB':[4,5], 'prodict': {'modbus': 1, 'iec104': 1}, 'freq': 100}, ...]
        :return: Network object
        """
        self.net = []
        ips = self.ipList(n)
        macs = self.macList(n)
        devices = []
        for ip, mac, type in zip(ips, macs, typeList):
            devices.append(Node(ip, mac, type))
        for rule in rules:
            self.net.append(Connection([devices[x-1] for x in rule['zoneA']], [devices[x-1] for x in rule['zoneB']],
                            rule['prodict'], rule['freq']))

    def ipList(self, n):
        """
        :param n: number of devices
        :return: a list of ip addresses
        """
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

    def macList(self, n):
        """
        :param n: number of devices
        :return: a list of mac addresses
        """
        mac_list = []
        for i in range(n):
            mac = [0x52, 0x54, 0x00, np.random.randint(0x00, 0x7f), np.random.randint(0x00, 0xff),
                   np.random.randint(0x00, 0xff)]
            mac_list.append(''.join(map(lambda x: "%02x" % x, mac)))
        return mac_list


if __name__ == '__main__':

    rules = [
        {'zoneA': range(1, 7), 'zoneB': range(19, 23), 'prodict': {'modbus': 1, 'iec104': 1, 'opcda': 1}, 'freq': 100},
        {'zoneA': range(1, 7), 'zoneB': range(23, 27), 'prodict': {'modbus': 1, 'iec104': 10, 'opcda': 1}, 'freq': 30}
        ]
    types = ['ws'] * 13 + ['server'] * 5 + ['plc'] * 12

    network = Network(30, types, rules)

    with open('config/test.json', 'w') as f:
        json.dump(network.net[0].toDict(), f, indent=4, sort_keys=True)