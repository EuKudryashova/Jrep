__author__ = 'kudryashova'
import subprocess
import queries
import libvirt
import logging
import workerAMQP

worker = None


def createBridge(br_name, **kwargs):
    """Create bridge, libvirt network add range of allowed IPs"""
    subprocess.call(['brctl', 'addbr', br_name])
    id = queries.addBridge(br_name)
    ip = '192.168.%d.1' % id
    subprocess.call(['ifconfig', br_name, ip, 'netmask',
                     '255.255.255.0', 'up'])
    queries.addRangeIP(id)
    netConfig = {'brname': br_name, 'ipaddr': ip, 'netmask': '255.255.255.0'}
    defineNetwork(netConfig)
    start = ip[:-1] + '2'
    end = ip[:-1] + '10'
    addDHCPrange(br_name, start, end)
    return 'Bridge %s with address %s was successfully created' % (br_name, ip)


def delBridge(br_name, **kwargs):
    """Delete bridge, network assigned to it"""
    id = queries.getBridgeIDbyName(br_name)
    if not queries.checkIfBridgeFree(id):
        raise RuntimeError('Attempt to delete not empty bridge')
    delConfBridge(id)
    subprocess.call(['ifconfig', br_name, 'down'])
    subprocess.call(['brctl', 'delbr', br_name])
    undefineNetwork(br_name)
    queries.delRangeIP(id)
    queries.delBridge(br_name)
    return 'Bridge %s was destroyed' % br_name


def defineNetwork(netConfig, **kwargs):
    """Define virtual network for libvirt domains"""
    con = getConnection()
    xmlConfig = open('net.xml').read()
    xmlConfig = xmlConfig.format(**netConfig)
    net = con.networkDefineXML(xmlConfig)
    net.create()


def undefineNetwork(net_name, **kwargs):
    """Delete virtual network for libvirt domains"""
    con = getConnection()
    net = con.networkLookupByName(net_name)
    if net.isActive():
        net.destroy()
    net.undefine()


def addDHCPrange(br_name, start_range, end_range):
    """Change configuration of dnsmasq and restart it"""
    conf_file = open('dhcp.conf', 'a')
    conf = 'dhcp-range=interface:%s,%s,%s,255.255.255.0\n' % (br_name,
                                                              start_range,
                                                              end_range)
    conf_file.write(conf)
    conf_file.close()
    subprocess.call(['/etc/init.d/dnsmasq', 'restart'])


def addDHCPhost(mac, ip, **kwargs):
    """Add static IP config for host to DHCP server"""
    conf_file = open('dhcp.conf', 'a')
    conf = 'dhcp-host=%s,%s\n'% (mac, ip)
    conf_file.write(conf)
    conf_file.close()
    subprocess.call(['/etc/init.d/dnsmasq', 'restart'])


def delConfBridge(id):
    """Del config of dnsmasq and restarts it"""
    conf = open('dhcp.conf', 'r')
    lines = conf.readlines()
    ip = '192.168.%d.' % id
    res = filter(lambda l: ip not in l, lines)
    conf = open('dhcp.conf', 'w')
    conf.writelines(res)
    conf.close()


def delConfHost(mac):
    """Del assigned static address for host"""
    conf = open('dhcp.conf', 'r')
    lines = conf.readlines()
    res = filter(lambda l: mac not in l, lines)
    conf = open('dhcp.conf', 'w')
    conf.writelines(res)
    conf.close()


def getConnection():
    """Open connection to emulator"""
    con = libvirt.open('qemu:///system')
    return con


def set_worker():
    global worker
    worker = worker or NetWorker()
    worker.run()

def stop_worker():
    worker.stop()


class NetWorker(workerAMQP.Worker):

    def __init__(self):
        self.logger = logging.getLogger('manageVM.net_manager')
        super(NetWorker, self).__init__()

    def run(self):
        self.define_queue('net_queue')
        self.define_queue('ins_queue')
        self.channel.basic_consume(self.process_mes, queue='net_queue')
        self.channel.basic_consume(self.process_mes, queue='ins_queue')
        self.start_consuming()