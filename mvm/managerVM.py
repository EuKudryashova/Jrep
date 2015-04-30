import libvirt
import getopt
import sys
import ConfigParser


def create(con, usrConfig):
    prc = ConfigParser.RawConfigParser()
    prc.read('defConfig.ini')
    defConfig = prc.defaults()
    defConfig.update(usrConfig)
    xmlConfig = open('template.xml').read()
    xmlConfig = xmlConfig.format(**defConfig)
    con.defineXML(xmlConfig)


def delete(dom):
    if dom.isActive():
        dom.destroy()
    dom.undefine()


def powerOn(dom):
    dom.create()


def powerOff(dom):
    if dom.isActive():
        dom.destroy()
    else:
        print 'Domain already unactive'


def reboot(dom):
    if dom.isActive():
        dom.reboot(0)
    else:
        print 'Domain already unactive'


def printHelp():
    print 'help'
    sys.exit()


def defDomain(con, name=None, domId=None):
    if name != None:
        return con.lookupByName(name)
    elif domId != None:
        return con.lookupById(int(domId))
    else:
        raise ValueError


def main(argv):
    actionMap = {'crt': create,
                 'del': delete,
                 'on': powerOn,
                 'off': powerOff,
                 'reb': reboot
        }
    args, opts = getopt.getopt(argv, 'h', ['action=', 'name=', 'id=',
                                           'source='])
    if '-h' in args:
        printHelp()
    usrConfig = {k[2:]: v for (k, v) in args}
    if not usrConfig.get('action') in actionMap:
        printHelp()
    con = libvirt.open("qemu:///system")
    if usrConfig['action'] == 'crt':
        if 'name' in usrConfig and 'source' in usrConfig:
            del usrConfig['action']
            create(con, usrConfig)
            return
    try:
        dom = defDomain(con, usrConfig.get('name'),
                        usrConfig.get('id'))
        actionMap[usrConfig['action']](dom)
    except ValueError:
        print 'use keys --name or --id to define a domain'


if __name__ == '__main__':
    main(sys.argv[1:])
