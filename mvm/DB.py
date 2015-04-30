import xml.etree.ElementTree
import libvirt
import sqlalchemy.types
import ConfigParser
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import *

Base = declarative_base()

class Enum(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.String(50)

    def __init__(self, *values, **kwargs):
        self.value_map = {i: values[i] for i in range(0,len(values))}
        super(Enum, self).__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        values = self.value_map.keys()
        if value in values:
            return self.value_map[value]
        raise KeyError('Allowed keys: ' + str(values) + ' v ' + str(value))

    def process_result_value(self, value, dialect):
        keys = self.value_map.keys()
        return [k for k in keys if self.value_map[k] == value][0]


class VM(Base):
    __tablename__ = 'vms'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    state = Column(Enum('Nostate', 'Running', 'Blocked', 'Paused', 'Shutdown',
                        'Shutoff', 'Crashed', 'Suspended', 'Last'))
    os_id = Column(Integer, ForeignKey('os.id'))
    os = relationship("OS", backref="vm")

    def __init__(self, name, os, state):
        self.name = name
        self.state = state
        self.os_id = os

    def __repr__(self):
        prc = ConfigParser.RawConfigParser()
        prc.read('defConfig.ini')
        states = dict(prc.items('STATESMAP'))
        state = states[str(self.state)]
        return "-vm %s -s %s -o + %s" % (self.name,
                                                     state,
                                                     self.os.name)


class OS(Base):
    __tablename__ = 'os'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    path = Column(String(50))

    def __init__(self, name, path):
        self.name = name
        self.path = path

    def __repr__(self):
        return "-o + %s + -i + %d" % (self.name, self.id)
