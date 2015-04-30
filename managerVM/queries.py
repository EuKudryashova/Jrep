import xml.etree.ElementTree
from sqlalchemy.orm import sessionmaker
from sqlalchemy import *
from DB import *


def getSession():
    Session = sessionmaker()
    engine = create_engine('mysql://root:password@localhost/VM_db', echo=True)
    session = Session(bind=engine)
    return session


def get_vm_list(session=None):
    session = session or getSession()
    res = session.query(VM).all()
    return res


def get_or_create(dom, session=None):
    session = session or getSession()
    vm = session.query(VM.name).filter(VM.name == dom.name()).scalar()
    if vm:
        return
    descr = xml.etree.ElementTree.fromstring(dom.XMLDesc(0))
    for src in descr.iter('source'):
        if 'file' in src.attrib.keys():
            source = src.attrib['file']
    os_name = session.query(OS.name).filter(OS.path == source).scalar()
    add_vm(dom.name(), os_name)


def add_vm(name, os, br_name, state=5, session=None):
    session = session or getSession()
    br_id = getBridgeIDbyName(br_name)
    os_id = session.query(OS.id).filter(OS.name == os).scalar()
    newVM = VM(name, os_id, state, br_id)
    session.add(newVM)
    session.commit()


def get_vm_state(vmname, session=None):
    session = session or getSession()
    res = session.query(VM.state).filter(VM.name == vmname).scalar()
    return res


def update_vm_state(vmname, state, session=None):
    session = session or getSession()
    session.query(VM).filter(VM.name == vmname).update({'state': state})
    session.commit()


def delete_vm(vmname, session=None):
    session = session or getSession()
    session.query(VM).filter(VM.name == vmname).delete()
    session.commit()


def add_os(osname, path, session=None):
    session = session or getSession()
    newOS = OS(osname, path)
    session.add(newOS)
    session.commit()


def get_os_list(session=None):
    session = session or getSession()
    res = session.query(OS).all()
    return res


def del_os(name, session=None):
    session = session or getSession()
    session.query(OS).filter(OS.name == name).delete()
    session.close()


def addRangeIP(id, session=None):
    session = session or getSession()
    for i in range(2, 10):
        ip = '192.168.%d.%d' % (id, i)
        print ip
        address = Address(ip, 'None', id)
        session.add(address)
    session.commit()


def delRangeIP(id, session=None):
    session = session or getSession()
    session.query(Address).filter(Address.br_id == id).delete()
    session.commit()


def assignIP(mac, bridge, session=None):
    session = session or getSession()
    br_id = getBridgeIDbyName(bridge)
    ip = session.query(Address.ip).filter(Address.br_id == br_id,
                                          Address.mac == 'None').all()[0][0]
    session.query(Address).filter(Address.ip == ip).update({'mac': mac})
    session.commit()
    return ip


def unAssignIP(mac, session=None):
    session = session or getSession()
    session.query(Address).filter(Address.mac == mac).update({'mac': 'None'})
    session.commit()
    pass

def addBridge(br_name, session=None):
    session = session or getSession()
    br = Bridge(br_name)
    session.add(br)
    session.commit()
    id = session.query(Bridge.id).filter(Bridge.name == br_name).scalar()
    return id


def delBridge(br_name, session=None):
    session = session or getSession()
    session.query(Bridge).filter(Bridge.name == br_name).delete()
    session.commit()


def getBridgeIDbyName(br_name, session=None):
    session = session or getSession()
    br_id = session.query(Bridge.id).filter(Bridge.name == br_name).scalar()
    return br_id


def checkIfBridgeFree(br_id, session=None):
    session = session or getSession()
    res = session.query(Address).filter(Address.br_id == br_id,
                                        Address.mac != 'None').all()
    return not res