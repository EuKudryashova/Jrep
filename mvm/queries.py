import xml.etree.ElementTree
import libvirt
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import *
from DB import *


def getSession():
    Session = sessionmaker()
    engine = create_engine('mysql://root:password@localhost/VM_db', echo=True)
    session = Session(bind=engine)
    return session


def get_vm_list(session=None):
    session = session or getSession()
    res =  session.query(VM).all()
    return res


def get_or_create(dom, session=None):
    session = session or getSession()
    vm = session.query(VM.name).filter(VM.name==dom.name()).scalar()
    if vm:
        return
    descr = xml.etree.ElementTree.fromstring(dom.XMLDesc(0))
    for src in descr.iter('source'):
        if 'file' in src.attrib.keys():
            source = src.attrib['file']
    os_name = session.query(OS.name).filter(OS.path==source).scalar()
    add_vm(dom.name(), os_name)


def add_vm(name, os, state=5, session=None):
    session = session or getSession()
    os_id = session.query(OS.id).filter(OS.name==os).scalar()
    newVM = VM(name, os_id, state)
    session.add(newVM)
    session.commit()


def get_vm_state(vmname, session=None):
    session = session or getSession()
    res = session.query(VM.state).filter(VM.name==vmname).scalar()
    return res



def update_vm_state(vmname, state, session=None):
    session = session or getSession()
    session.query(VM).filter(VM.name==vmname).update({'state': state})
    session.commit()


def delete_vm(vmname, session=None):
    session = session or getSession()
    session.query(VM).filter(VM.name==vmname).delete()
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
    session.query(OS).filter(OS.name==name).delete()
    session.close()
