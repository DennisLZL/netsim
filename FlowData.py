__author__ = 'dennis'

import numpy as np
from scipy.stats import rv_discrete
import datetime as dt


protocols = ['iec104', 'modbus', 'dnp3', 'opcda', 'profinetio', 'TIAS_TETRA', 's7', 'mms', 'udp', 'icmp', 'ftp', 'tcp']

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

    def commMsg(self, dest):
        """
        communicate with other node and generate flow data
        :param dest: other node
        :return: a list of flow data
        """
        commpro = list(set(self.proset.keys()).intersection(set(dest.proset.keys())))
        wt = np.array([node1.proset[x] for x in commpro]) + np.array([node2.proset[x] for x in commpro])
        wt /= float(wt.sum())
        n = np.random.randint(1, 100)  # number of communications to generate

        proid = rv_discrete(values=(range(len(commpro)), wt)).rvs(size=n)
        dataflow = []

        for i in range(n):
            protocol = commpro[proid[i]]

            if protocol == 'iec104':
                msg = iec104_sample[np.random.randint(len(iec104_sample))]

            if protocol == 'modbus':
                msg = modbus_sample[np.random.randint(len(modbus_sample))]

            if protocol == 'dnp3':
                msg = dnp3_sample[np.random.randint(len(dnp3_sample))]

            if protocol == 'opcda':
                msg = opcda_sample[np.random.randint(len(opcda_sample))]

            if protocol == 'profinetio':
                msg = profinetio_sample[np.random.randint(len(profinetio_sample))]

            dataflow.append(', '.join([self.ip, dest.ip, msg, dt.datetime.now().strftime('%m/%d/%Y-%H:%M:%S.%f'),
                                       '1', self.mac, dest.mac]))
            dataflow.append(', '.join([dest.ip, self.ip, msg, dt.datetime.now().strftime('%m/%d/%Y-%H:%M:%S.%f'),
                                       '1', dest.mac, self.mac]))

        return dataflow


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
    # ips = ipList(2)
    # macs = macList(2)
    # node1 = Node(ips[0], macs[0], {'tcp': 1., 'iec104': 1., 'modbus': 1.}, 'workStation')
    # node2 = Node(ips[1], macs[1], {'iec104': 1., 'modbus': 1.}, 'PLC')
    #
    # data = node1.commMsg(node2)
    # for m in data:
    #     print m

    # with open('config/profinetiosample', 'w') as f:
    #     for item in profinetio_sample:
    #         f.write('%s\n' % item)

    with open('config/iec104sample', 'r') as f:
        iec104_sample = f.read().splitlines()
    with open('config/modbussample', 'r') as f:
        modbus_sample = f.read().splitlines()
    with open('config/opcdasample', 'r') as f:
        opcda_sample = f.read().splitlines()
    with open('config/profinetiosample') as f:
        profinetio_sample = f.read().splitlines()

    print iec104_sample
    print modbus_sample
    print opcda_sample
    print profinetio_sample
