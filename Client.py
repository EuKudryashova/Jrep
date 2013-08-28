"""
Client module forms requests and process obtained responses.
"""
import getopt
import sys
import simplejson
import logging
import ConfigParser
from webob import Request
import confLogging


def printHelp():
    print 'Usage:'
    print 'Use -h to display help'
    print 'Use --action to define action. Allowed actions:'
    print '"crt" - create VM; "del" - delete existing VM;'
    print '"on", "off", "reboot" - change state of existing VM;'
    print 'Allowed arguments: --name - name of existing VM, '
    print '--id  - id of existing VM, --os - OS for new VM'


def main(argv):
    args, opts = getopt.getopt(argv, 'h', ['action=', 'name=',
                                           'id=', 'os='])
    keys = [arg[0] for arg in args]
    if '-h' in keys or not '--action' in keys:
        return printHelp()
    prc = ConfigParser.RawConfigParser()
    prc.read('defConfig.ini')
    actionMap = dict(prc.items('ACTIONMAP'))
    usrConfig = {k[2:]: v for (k, v) in args}
    if not usrConfig['action'] in actionMap:
        return printHelp()
    req = Request.blank('http://localhost:8080')
    req.content_type = 'application/json'
    req.body = simplejson.dumps(usrConfig)
    resp = req.get_response()
    res = simplejson.loads(resp.body)
    logger = logging.getLogger('manageVM.client')
    logger = confLogging.configLog(logger)
    logger.info(res['result'])
    if res['error'] != None:
        logger.error(res['message'])
        printHelp()


if __name__ == '__main__':
    main(sys.argv[1:])
