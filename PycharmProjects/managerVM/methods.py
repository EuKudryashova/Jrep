"""
Module contains allowed methods to manipulate VMs.
"""
import logging
import ConfigParser
import xml.etree.ElementTree as ET
import libvirt
import queries
import workerAMQP

worker = None


def create(**usrConfig):
    """Creates VM of given type"""
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
    worker.send_mes({'act': 'add_host', 'mac': mac, 'ip': ip})
    res = 'New VM {} was successfully created'.format(name)
    return res


def defineDomain(name=None, domId=None, con=None):
    """Define domain by given name or id."""
    con = con or getConnection()
    x = None
    if name:
        x = con.lookupByName(name)
    elif domId:
        x = con.lookupById(int(domId))
    if x:
        queries.get_or_create(x)
    return x


def delete(name, **kwargs):
    """Delete given libvirt domain"""
    dom = defineDomain(name)
    if queries.get_vm_state(name) == 1:
        dom.destroy()
    mac = getMAC(name)
    queries.unAssignIP(mac)
    queries.delete_vm(name)
    worker.send_mes({'act': 'del_host', 'mac': mac})
    res = 'VM {} was destroyed'.format(name)
    dom.undefine()
    return res


def powerOn(name, **kwargs):
    """PowerOn given libvirt domain"""
    dom = defineDomain(name)
    dom.create()
    queries.update_vm_state(name, 1)
    res = 'VM {} powered on'.format(name)
    return res


def powerOff(name, **kwargs):
    """PowerOff given libvirt domain"""
    dom = defineDomain(name)
    if queries.get_vm_state(name) == 1:
        dom.destroy()
        queries.update_vm_state(name, 5)
    else:
        logger = logging.getLogger('manageVM.compute')
        logger.warning('Attempt to power off unactive domain')
    res = 'VM {} powered off'.format(name)
    return res


def reboot(name, **kwargs):
    """Reboot given libvirt domain"""
    dom = defineDomain(name)
    if queries.get_vm_state(name) == 1:
        dom.reboot(0)        
    else:
        logger = logging.getLogger('manageVM.processing')
        logger.warning('Attempt to reboot unactive domain')
    res = 'VM {} rebooted'.format(name)
    return res


def get_vm_state(name, **kwargs):
    """Load from DB code of state of VM and return state"""
    dom = defineDomain(name)
    prc = ConfigParser.RawConfigParser()
    prc.read('defConfig.ini')
    states = dict(prc.items('STATESMAP'))
    name = dom.name()
    key_state = str(queries.get_vm_state(name))
    state = states[key_state]
    return "VM %s state: %s".format(name, state)


def get_os_list(**kwargs):
    """Return list of available OS"""
    os_list = queries.get_os_list()
    result = ''
    for os in os_list:
        os = str(os)
        result += os + '\n'
    return result


def get_vm_list(**kwargs):
    """Return list of available VMs"""
    list_vm = queries.get_vm_list()
    result = ''
    for vm in list_vm:
        vm = str(vm)
        result += vm + '\n'
    return result


def getConnection():
    """Open connection to emulator"""
    con = libvirt.open('qemu:///system')
    return con


def getMAC(name, con=None, **kwargs):
    """Load from XML description of domain MAC-address"""
    con = con or getConnection()
    descr = ET.fromstring(con.lookupByName(name).XMLDesc(0))
    for mac in descr.iter('mac'):
        mac_addr = mac.attrib['address']
    return mac_addr


def set_worker():
    """Sets worker to deal with queries to compute manager"""
    global worker
    worker = worker or VMWorker()
    worker.run()


class VMWorker(workerAMQP.Worker):

    def __init__(self):
        self.logger = logging.getLogger('manageVM.compute')
        super(VMWorker, self).__init__()

    def run(self):
        self.define_queue('vm_s')
        self.define_queue('s_vm')
        self.define_queue('vm_net')
        self.define_queue('net_vm')
        self.do_basic_consume(self.process_mes, queue='s_vm')
        self.do_basic_consume(self.receive_res, queue='net_vm')
        self.start_consuming()