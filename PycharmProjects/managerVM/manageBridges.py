__author__ = 'kudryashova'
import subprocess
import queries
import libvirt
import logging
import workerAMQP

worker = None


def createBridge(bridge, **kwargs):
    """Create bridge, libvirt network add range of allowed IPs"""
    subprocess.call(['brctl', 'addbr', bridge])
    id = queries.addBridge(bridge)
    ip = '192.168.%d.1' % id
    subprocess.call(['ifconfig', bridge, ip, 'netmask',
                     '255.255.255.0', 'up'])
    queries.addRangeIP(id)
    netConfig = {'brname': bridge, 'ipaddr': ip, 'netmask': '255.255.255.0'}
    defineNetwork(netConfig)
    start = ip[:-1] + '2'
    end = ip[:-1] + '10'
    addDHCPrange(bridge, start, end)
    return 'Bridge %s with address %s was successfully created' % (bridge, ip)


def delBridge(bridge, **kwargs):
    """Delete bridge, network assigned to it"""
    id = queries.getBridgeIDbyName(bridge)
    if not queries.checkIfBridgeFree(id):
        raise RuntimeError('Attempt to delete not empty bridge')
    delConfBridge(id)
    subprocess.call(['ifconfig', bridge, 'down'])
    subprocess.call(['brctl', 'delbr', bridge])
    undefineNetwork(bridge)
    queries.delRangeIP(id)
    queries.delBridge(bridge)
    return 'Bridge %s was destroyed' % bridge


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
    conf = 'dhcp-host=%s,%s\n' % (mac, ip)
    conf_file.write(conf)
    conf_file.close()
    subprocess.call(['/etc/init.d/dnsmasq', 'restart'])
    return 'DHCP host with mac ' + mac + 'assigned to ip ' + ip


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
    return 'DHCP host with mac ' + mac + 'has no ip'


def getConnection():
    """Open connection to emulator"""
    con = libvirt.open('qemu:///system')
    return con


def set_worker():
    """Set AMQP worker for dealing with queries to network manager"""
    global worker
    worker = worker or NetWorker()
    worker.run()


class NetWorker(workerAMQP.Worker):

    def __init__(self):
        self.logger = logging.getLogger('manageVM.net_manager')
        super(NetWorker, self).__init__()

    def run(self):
        self.define_queue('s_net')
        self.define_queue('net_s')
        self.define_queue('vm_net')
        self.define_queue('net_vm')
        self.do_basic_consume(self.process_mes, 's_net')
        self.do_basic_consume(self.process_mes, 'vm_net')
        self.start_consuming()