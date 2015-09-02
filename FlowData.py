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

    def __init__(self, id, ip, mac, type):
        """
        :param id: device id
        :param ip: ip address
        :param mac: mac address
        :param type: device type, e.g. 'ws', 'plc', 'server'
        :return: Node object
        """
        self.id = id
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
        time = time.strftime('%m/%d/%Y-%H:%M:%S.%f')
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

    def __init__(self):
        self.net = []

    @classmethod
    def easyMake(cls, n, typeList, rules):
        """
        :param n: number of devices
        :param typeList: a list of device type
        :param rules: e.g. [{'zoneA':[1,2,3], 'zoneB':[4,5], 'prodict': {'modbus': 1, 'iec104': 1}, 'freq': 100}, ...]
        :return: Network object
        """
        mynet = cls()
        ips = mynet.ipList(n)
        macs = mynet.macList(typeList)
        devices = []
        ids = range(1, n+1)
        for i, ip, mac, t in zip(ids, ips, macs, typeList):
            devices.append(Node(i, ip, mac, t))

        for rule in rules:
            mynet.net.append(Connection([devices[x-1] for x in rule['zoneA']], [devices[x-1] for x in rule['zoneB']],
                                        rule['prodict'], rule['freq']))
        return mynet

    @classmethod
    def fileMake(cls, filepath):
        """
        construction from json file
        :param filepath: json file path
        :return: Network object
        """
        mynet = cls()
        with open(filepath, 'r') as f:
            nk = json.load(f, parse_float=True)
        for c in nk:
            zA = [Node(n['id'], n['ip'], n['mac'], n['type']) for n in c['zoneA']]
            zB = [Node(n['id'], n['ip'], n['mac'], n['type']) for n in c['zoneB']]
            mynet.net.append(Connection(zA, zB, c['prodict'], c['freq']))
        return mynet

    def toJson(self, filepath):
        """
        save network configurations to json file
        :param filepath: json file path
        :return: None
        """
        netlist = []
        for c in self.net:
            netlist.append(c.toDict())
        with open(filepath, 'w') as f:
            json.dump(netlist, f, sort_keys=True, indent=4)

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

    def networkFlowData(self, t0, tincr, tn):
        nc = len(self.net)
        trec = [t0] * nc
        t = t0
        data = []
        while t <= tn:
            for i in range(nc):
                if (t - trec[i]).total_seconds() * 1000 >= (1000 / self.net[i].freq):
                    data.extend(self.net[i].connComm(t))
                    trec[i] = t
            t += tincr
        return data

    def macList(self, typeList):
        """
        :param typeList: a list of device types
        :return: a list of mac addresses
        """
        wshead = [[0x00, 0x06, 0x1B], [0x00, 0x1A, 0xA0], [0x00, 0x1C, 0x23], [0x00, 0x22, 0x64]]
        serverhead = [[0x00, 0xF8, 0x1C], [0x00, 0xE0, 0xFC]]
        plchead = [[0x08, 0x00, 0x06], [0x28, 0x63, 0x36], [0x00, 0x0C, 0x81]]
        mac = []
        for t in typeList:
            if t == 'ws':
                mac.append(wshead[np.random.randint(len(wshead))] +
                                [np.random.randint(0x00, 0xff), np.random.randint(0x00, 0xff), np.random.randint(0x00, 0xff)])
            if t == 'plc':
                mac.append(plchead[np.random.randint(len(plchead))] +
                                [np.random.randint(0x00, 0xff), np.random.randint(0x00, 0xff), np.random.randint(0x00, 0xff)])
            if t == 'server':
                mac.append(serverhead[np.random.randint(len(serverhead))] +
                                [np.random.randint(0x00, 0xff), np.random.randint(0x00, 0xff), np.random.randint(0x00, 0xff)])
        mac_list = [''.join(map(lambda x: "%02X" % x, m)) for m in mac]
        return mac_list



if __name__ == '__main__':

    # 30 devices

    # types = ['ws'] * 13 + ['server'] * 5 + ['plc'] * 12
    # rules = [
    #     {'zoneA': range(1, 7), 'zoneB': range(19, 23), 'prodict': {'modbus': 1, 'iec104': 1, 'opcda': 1}, 'freq': 100},
    #     {'zoneA': range(1, 7), 'zoneB': range(23, 27), 'prodict': {'modbus': 1, 'iec104': 10, 'opcda': 1}, 'freq': 30},
    #     {'zoneA': range(7, 11), 'zoneB': range(19, 23), 'prodict': {'iec104': 3, 'modbus': 1, 'dnp3': 3, 'opcda': 1}, 'freq': 50},
    #     {'zoneA': range(11, 14), 'zoneB': range(23, 27), 'prodict': {'iec104': 3, 'modbus': 1, 'dnp3': 3, 'opcda': 1}, 'freq': 10},
    #     {'zoneA': range(11, 14), 'zoneB': range(27, 31), 'prodict': {'TIAS_TETRA': 1, 's7':1, 'mms': 1}, 'freq': 10},
    #     {'zoneA': range(7, 11), 'zoneB': range(27, 31), 'prodict': {'TIAS_TETRA': 2, 's7':2, 'mms': 2, 'modbus': 1, 'iec104': 1, 'opcda': 1}, 'freq': 50},
    #     {'zoneA': range(11, 14), 'zoneB': range(19, 23), 'prodict': {'opcda': 1}, 'freq': 10},
    #     {'zoneA': range(11, 14), 'zoneB': range(14, 19), 'prodict': {'udp': 1, 'ftp': 2, 'tcp': 1}, 'freq': 10},
    #     {'zoneA': range(7, 11), 'zoneB': range(14, 19), 'prodict': {'udp': 1, 'ftp': 3, 'tcp': 1}, 'freq': 20}
    #     ]
    #
    # net = Network.easyMake(30, types, rules)
    #
    # net.toJson('config/config.json')

    # net = Network.fileMake('config/config.json')
    #
    # t0 = dt.datetime.now()
    # tincr = dt.timedelta(milliseconds=1)
    # # tn = t0 + dt.timedelta(milliseconds=1500)
    # tn = t0 + dt.timedelta(minutes=30)
    # data = net.networkFlowData(t0, tincr, tn)
    #
    # with open('resource/flowdata.csv', 'w') as f:
    #     for line in data[:-1]:
    #         f.write('%s\n' % line)
    #     f.write('%s' % data[-1])

    # 100 devices

    # types = ['ws'] * 50 + ['plc'] * 50
    # rules = [
    #     {'zoneA': range(1, 21), 'zoneB': range(51, 75), 'prodict': {'modbus':1, 'iec104': 1, 'opcda': 1}, 'freq': 300},
    #     {'zoneA': range(1, 21), 'zoneB': range(76, 101), 'prodict': {'iec104': 3, 'modbus': 1, 'dnp3': 3, 'opcda': 1}, 'freq': 100},
    #     {'zoneA': range(21, 51), 'zoneB': range(51, 75), 'prodict': {'TIAS_TETRA': 1, 's7': 1, 'mms': 1}, 'freq': 200},
    #     {'zoneA': range(21, 51), 'zoneB': range(76, 101), 'prodict': {'TIAS_TETRA': 2, 's7': 2, 'mms': 2, 'modbus': 1, 'iec104': 1, 'opcda': 1}, 'freq': 50}
    # ]
    #
    # net = Network.easyMake(100, types, rules)
    # net.toJson('config/config100v2.json')

    net = Network.fileMake('config/config100v2.json')

    t0 = dt.datetime.now()
    tincr = dt.timedelta(milliseconds=1)
    # tn = t0 + dt.timedelta(milliseconds=1500)
    tn = t0 + dt.timedelta(minutes=10)
    data = net.networkFlowData(t0, tincr, tn)

    with open('resource/flowdata100v2.csv', 'w') as f:
        for line in data[:-1]:
            f.write('%s\n' % line)
        f.write('%s' % data[-1])
