import libvirt
import getopt
import sys


def create(con, usrConfig):
    defConfig = {'domType': 'qemu', 'mem': '119200', 'curMem': '119200',
             'typeOs': 'hvm', 'emul': '/usr/bin/qemu-system-x86_64',
             'diskType': 'file', 'diskDev': 'disk', 'drvrName': 'qemu',
             'drvrType': 'qcow2', 'targetDev': 'hda', 'vcpu': '1'}
    defConfig.update(usrConfig)
    print defConfig
    xmlConfig = open('template.xml').read()
    xmlConfig = xmlConfig.format(**defConfig)
    print xmlConfig
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
    print ''
    sys.exit()


def defDomain(con, name=None, domId=None):
    if name != None:
        return con.lookupByName(name)
    elif domId !=None:
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
    usrConfig = dict(args)
    usrConfig = {k[2:]: usrConfig[k] for k in usrConfig}
    if usrConfig.get('action') in actionMap:
        con = libvirt.open("qemu:///system")        
        if usrConfig['action']=='crt':
            if 'name' in usrConfig and 'source' in usrConfig:
                del usrConfig['action']
                create(con, usrConfig)
        else:
            try:
                dom = defDomain(con, usrConfig.get('name'),
                                usrConfig.get('id'))
                actionMap[usrConfig['action']](dom)
            except ValueError:
                print 'use keys --name or --id to define a domain'
    else: printHelp()
            

if __name__ == '__main__':
    main(sys.argv[1:])
