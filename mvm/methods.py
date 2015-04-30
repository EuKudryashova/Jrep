"""
Module contains allowed methods to manipulate VMs.
"""
import libvirt
import logging
import ConfigParser
import queries

def create(con, usrConfig):
    """Creates VM of given type"""
    prc = ConfigParser.RawConfigParser()
    prc.read('defConfig.ini')
    defConfig = dict(prc.items('DEFAULTVM'))
    os = usrConfig['os']
    name = usrConfig['name']
    usrConfig['source'] = prc.get('OSPATHMAP', os)
    del usrConfig['os']
    defConfig.update(usrConfig)
    xmlConfig = open('template.xml').read()
    xmlConfig = xmlConfig.format(**defConfig)
    con.defineXML(xmlConfig)
    queries.add_vm(name,os)
    res = 'New VM {} was successfully created'.format(name)
    return res


def delete(dom):
    """Delete given libvirt domain"""
    name = dom.name()
    if queries.get_vm_state(name) == 1:
        dom.destroy()
    dom.undefine()
    queries.delete_vm(name)
    res = 'VM {} was destroyed'.format(name)
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
    prc = ConfigParser.RawConfigParser()
    prc.read('defConfig.ini')
    states = dict(prc.items('STATESMAP'))
    name = dom.name()
    key_state = str(queries.get_vm_state(name))
    state =  states[key_state]
    return "VM %s state: %s".format(name, state)


def get_os_list():
    oslist = queries.get_os_list()
    result = ''
    
    for os in oslist:
        os = str(os)
        result += os + ', '
    return result


def get_vm_list():
    listvm = queries.get_vm_list()
    result = ''
    for vm in listvm:
        vm = str(vm)
        result += vm + ', '
    return result


# add_os del_os  ? 
