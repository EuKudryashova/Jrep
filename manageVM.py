import sys
import libvirt
import getopt


def create(con, userConfig):
    defConfig = {'domType': 'qemu', 'mem': '119200', 'curMem': '119200',
                 'vcpu': '1', 'arcType': 'x86_64', 'virType': 'hvm',
                 'bootDev': 'cdrom', 'emul': '/usr/bin/qemu-system-x86_64',
                 'diskType': 'file', 'diskDev': 'disk', 'targDev': 'hda',
                 'drvrName': 'qemu', 'drvrType': 'qcow2'}
    defConfig.update(userConfig)
    xmlConfig = open('template.xml').read()
    xmlConfig = xmlConfig.format(**defConfig)
    con.defineXML(xmlConfig)


def delete(dom):
    if dom.isActive():
        dom.destroy()
    dom.undefine()


def reboot(dom):
    dom.reboot(0)


def powerOn(dom):
    dom.create()


def powerOff(dom):
    if dom.isActive():
        dom.shutdown()
    else:
        print 'Domain already stopped'


def printHelp():
    print 'use -h for help'
    print '--action=[WORD] on - power on VM, off - power off VM'
    print 'reb - reboot VM, crt - create VM, del - delete VM'
    print 'allowed parameters: --name=[WORD], --id=[NUMBER], --source=[PATH]'
    sys.exit()


def defDomain(con, dom_name=None, dom_id=None):
    if dom_name != None:
        return con.lookupByName(dom_name)
    elif dom_id != None:
        return con.lookupByID(int(dom_id))
    else:
        raise ValueError


def main(argv):
    act_map = {
        'on': powerOn,
        'off': powerOff,
        'del': delete,
        'reb': reboot,
        'crt': create,
    }
    opts, args = getopt.getopt(argv, 'h', ['action=', 'name=',
                                             'source=', 'id='])
    opts = dict(opts)
    if '-h' in opts:
        printHelp()
    con = libvirt.open("qemu:///system")
    if '--action' in opts and opts['--action'] in act_map:
        if opts['--action'] == 'crt':
            if '--name' in opts and '--source' in opts:
                del opts['--action']
                opts = {k[2:]: opts[k] for k in opts}
                create(con, opts)
        else:
            try:
                domain = defDomain(con, opts.get('--name'), opts.get('--id'))
                act_map.get(opts['--action'])(domain)
            except ValueError:
                print 'to define a domain name or id should be entered'
    else:
        printHelp()


if __name__ == '__main__':
    main(sys.argv[1:])
