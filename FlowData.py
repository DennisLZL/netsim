__author__ = 'dennis'

import numpy as np
from scipy.stats import rv_discrete
import datetime as dt


protocols = ['iec104', 'modbus', 'dnp3', 'BX_03', 'BX_04', 'BX_13', 'opcda',
             'profinetio', 'TIAS_TETRA', 's7', 'mms', 'udp', 'icmp', 'ftp', 'tcp']

iec104_sample = ['{protocol:iec104,asdu_type:107,causetx_type:30}',
           '{protocol:iec104,asdu_type:50,causetx_type:6}',
           '{protocol:iec104,asdu_type:50,causetx_type:7}',
           '{protocol:iec104,asdu_type:107,causetx_type:30}',
           '{protocol:iec104,asdu_type:49,causetx_type:7}',
           '{protocol:iec104,asdu_type:45,causetx_type:6}']

modbus_sample = ['{protocol:modbus,func:1}',
                 '{protocol:modbus,func:2}',
                 '{protocol:modbus,func:3}',
                 '{protocol:modbus,func:99}',
                 '{protocol:modbus,func:5,startaddr:1031,endaddr:1031}',
                 '{protocol:modbus,func:5,startaddr:1024,endaddr:1024}',
                 '{protocol:modbus,func:3,startaddr:1000,endaddr:1}',
                 '{protocol:modbus,func:1,length:22,type:good}',
                 '{protocol:modbus,func:1,length:32,type:good}']
dnp3_sample = []


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
                iec104msg = iec104_sample[np.random.randint(len(iec104_sample))]
                dataflow.append(', '.join([self.ip, dest.ip, iec104msg, dt.datetime.now().strftime('%m/%d/%Y-%H:%M:%S.%f'),
                                      '1', self.mac, dest.mac]))
                dataflow.append(', '.join([dest.ip, self.ip, iec104msg, dt.datetime.now().strftime('%m/%d/%Y-%H:%M:%S.%f'),
                                      '1', dest.mac, self.mac]))
            if protocol == 'modbus':
                modbusmsg = modbus_sample[np.random.randint(len(modbus_sample))]
                dataflow.append(', '.join([self.ip, dest.ip, modbusmsg, dt.datetime.now().strftime('%m/%d/%Y-%H:%M:%S.%f'),
                                      '1', self.mac, dest.mac]))
                dataflow.append(', '.join([dest.ip, self.ip, modbusmsg, dt.datetime.now().strftime('%m/%d/%Y-%H:%M:%S.%f'),
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
    ips = ipList(2)
    macs = macList(2)
    node1 = Node(ips[0], macs[0], {'tcp': 1., 'iec104': 1., 'modbus': 1.}, 'workStation')
    node2 = Node(ips[1], macs[1], {'iec104': 1., 'modbus': 1.}, 'PLC')

    data = node1.commMsg(node2)
    for m in data:
        print m
