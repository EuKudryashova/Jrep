"""
Module contains allowed methods to manipulate VMs.
"""
import libvirt
import logging
import ConfigParser


def create(con, usrConfig):
    """Creates VM of given type"""
    prc = ConfigParser.RawConfigParser()
    prc.read('defConfig.ini')
    defConfig = dict(prc.items('DEFAULTVM'))
    usrConfig['source'] = prc.get('OSPATHMAP', usrConfig['os'])
    del usrConfig['os']
    defConfig.update(usrConfig)
    xmlConfig = open('template.xml').read()
    xmlConfig = xmlConfig.format(**defConfig)
    con.defineXML(xmlConfig)
    name = usrConfig['name']
    return 'New VM {} was successfully created'.format(name)


def delete(dom):
    """Delete given libvirt domain"""
    name = dom.name()
    if dom.isActive():
        dom.destroy()
    dom.undefine()
    return 'VM {} was destroyed'.format(name)


def powerOn(dom):
    """PowerOn given libvirt domain"""
    name = dom.name()
    dom.create()
    return 'VM {} powered on'.format(name)


def powerOff(dom):
    """PowerOff given libvirt domain"""
    name = dom.name()
    if dom.isActive():
        dom.destroy()
    else:
        logger = logging.getLogger('manageVM.processing')
        logger.warning('Attempt to power off unactive domain')
    return 'VM {} powered off'.format(name)


def reboot(dom):
    """Reboot given libvirt domain"""
    name = dom.name()
    if dom.isActive():
        dom.reboot(0)
    else:
        logger = logging.getLogger('manageVM.processing')
        logger.warning('Attempt to reboot unactive domain')
    return 'VM {} rebooted'.format(name)
