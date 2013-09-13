"""
Module contains allowed methods to manipulate VMs.
"""
import libvirt
import logging
import ConfigParser
import xml.etree.ElementTree as ET
import queries
import manageBridges

def create(usrConfig, con=None):    #usrconfig
    """Creates VM of given type"""
    if not con:
        con = getConnection()
    prc = ConfigParser.RawConfigParser()
    prc.read('defConfig.ini')
    defConfig = dict(prc.items('DEFAULTVM'))
    os = usrConfig['os']
    name = usrConfig['name']
    bridge = usrConfig['bridge']
    usrConfig['source'] = prc.get('OSPATHMAP', os)
    del usrConfig['os']
    defConfig.update(usrConfig)
    xmlConfig = open('template.xml').read()
    xmlConfig = xmlConfig.format(**defConfig)
    con.defineXML(xmlConfig)
    queries.add_vm(name, os, bridge)
    mac = getMAC(name)
    ip = queries.assignIP(mac, bridge)
    manageBridges.addDHCPhost(mac, ip)
    res = 'New VM {} was successfully created'.format(name)
    return res


def delete(dom):
    """Delete given libvirt domain"""
    name = dom.name()
    if queries.get_vm_state(name) == 1:
        dom.destroy()
    mac = getMAC(name)
    queries.unAssignIP(mac)
    queries.delete_vm(name)
    manageBridges.delConfHost(mac)
    res = 'VM {} was destroyed'.format(name)
    dom.undefine()
    return res


def powerOn(dom):
    """PowerOn given libvirt domain"""
    name = dom.name()
    dom.create()
    queries.update_vm_state(name, 1)
    res = 'VM {} powered on'.format(name)
    return res


def powerOff(dom):
    """PowerOff given libvirt domain"""
    name = dom.name()
    if queries.get_vm_state(name) == 1:
        dom.destroy()
        queries.update_vm_state(name, 5)       
    else:
        logger = logging.getLogger('manageVM.processing')
        logger.warning('Attempt to power off unactive domain')
    res = 'VM {} powered off'.format(name)
    return res


def reboot(dom):
    """Reboot given libvirt domain"""
    name = dom.name()
    if queries.get_vm_state(name) == 1:
        dom.reboot(0)        
    else:
        logger = logging.getLogger('manageVM.processing')
        logger.warning('Attempt to reboot unactive domain')
    res = 'VM {} rebooted'.format(name)
    return res


def get_vm_state(dom):
    """Load from DB code of state of VM and return state"""
    prc = ConfigParser.RawConfigParser()
    prc.read('defConfig.ini')
    states = dict(prc.items('STATESMAP'))
    name = dom.name()
    key_state = str(queries.get_vm_state(name))
    state = states[key_state]
    return "VM %s state: %s".format(name, state)


def get_os_list():
    """Return list of available OS"""
    os_list = queries.get_os_list()
    result = ''
    for os in os_list:
        os = str(os)
        result += os + ', '
    return result


def get_vm_list():
    """Return list of available VMs"""
    list_vm = queries.get_vm_list()
    result = ''
    for vm in list_vm:
        vm = str(vm)
        result += vm + ', '
    return result


def defineNetwork(netConfig, con=None):
    """Define virtual network for libvirt domains"""
    con = con or getConnection()
    xmlConfig = open('net.xml').read()
    xmlConfig = xmlConfig.format(**netConfig)
    net = con.networkDefineXML(xmlConfig)
    net.create()


def undefineNetwork(net_name, con=None):
    """Delete virtual network for libvirt domains"""
    con = con or getConnection()
    net = con.networkLookupByName(net_name)
    if net.isActive():
        net.destroy()
    net.undefine()


def getConnection():
    """Open connection to emulator"""
    con = libvirt.open('qemu:///system')
    return con


def getMAC(vmname, con=None):
    """Load from XML description of domain MAC-address"""
    con = con or getConnection()
    descr = ET.fromstring(con.lookupByName(vmname).XMLDesc(0))
    for mac in descr.iter('mac'):
        mac_addr = mac.attrib['address']
    return mac_addr