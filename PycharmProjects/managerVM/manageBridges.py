__author__ = 'kudryashova'
import subprocess
import queries
import methods


def createBridge(br_name):
    """Create bridge, libvirt network add range of allowed IPs"""
    subprocess.call(['brctl', 'addbr', br_name])
    id = queries.addBridge(br_name)
    ip = '192.168.%d.1'% (id)
    subprocess.call(['ifconfig', br_name, ip, 'netmask',
                     '255.255.255.0', 'up'])
    queries.addRangeIP(id)
    netConfig = {'brname': br_name, 'ipaddr': ip, 'netmask': '255.255.255.0'}
    methods.defineNetwork(netConfig)
    start = ip[:-1] + '2'
    end = ip[:-1] + '10'
    addDHCPrange(br_name, start, end)
    return 'Bridge %s with address %s was successfully created' % (br_name,
                                                                   ip)


def delBridge(br_name):
    """Delete bridge, network assigned to it"""
    id = queries.getBridgeIDbyName(br_name)
    if not queries.checkIfBridgeFree(id):
        raise RuntimeError('Attempt to delete not empty bridge')
    delConfBridge(id)
    subprocess.call(['ifconfig',br_name, 'down'])
    subprocess.call(['brctl', 'delbr', br_name])
    methods.undefineNetwork(br_name)
    queries.delRangeIP(id)
    queries.delBridge(br_name)
    return 'Bridge %s was destroyed' % br_name


def addDHCPrange(br_name, start_range, end_range):
    """Change configuration of dnsmasq and restart it"""
    conf_file = open('dhcp.conf', 'a')
    conf = 'dhcp-range=interface:%s,%s,%s,255.255.255.0\n' % (br_name,
                                                              start_range,
                                                              end_range)
    conf_file.write(conf)
    conf_file.close()
    subprocess.call(['/etc/init.d/dnsmasq', 'restart'])


def addDHCPhost(mac, ip):
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

