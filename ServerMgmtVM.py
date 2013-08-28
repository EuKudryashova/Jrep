"""
Module make server to manage VMs,  ...
"""
import logging
import simplejson
from wsgiref.simple_server import make_server
import ConfigParser
import libvirt
import webob
import methods
import confLogging


class ManageVM(object):
    """Application for serving.

    Allows manipulations of VM's images, such as creating, destroying,
    changing status of given VM.
    """

    def __init__(self):
        """Initialise serving application."""
        self.con = libvirt.open("qemu:///system")

    def __call__(self, environ, start_response):
        """Loads  given request, process it and return response"""
        req = webob.Request(environ)
        resp = self.processReq(req)
        return resp(environ, start_response)

    def processReq(self, req):
        """Processing given request.

        Process required method on VM and return formed response
        dependent on results of operation.
        """
        json = simplejson.loads(req.body)
        resp = webob.Response(status=200, content_type='application/json')
        try:
            action = json['action']
            del json['action']
        except KeyError as e:
            return self.handleError(req, resp, e)
        meth = self.defineMethod(action)
        try:
            resp = self.processMeth(meth, json, resp)
        except libvirt.libvirtError as e:
            return self.handleError(req, resp, e)
        logger = logging.getLogger('manageVM.server')
        logger.info('Operation ' + meth.__name__ +
                         ' from host ' + req.client_addr + ' completed.')
        return resp

    def defineDomain(self, name=None, domId=None):
        """Define domain by given name or id."""
        if name != None:
            return self.con.lookupByName(name)
        elif domId != None:
            return self.con.lookupById(int(domId))

    def defineMethod(self, act):
        """Define required method, get it from module with allowed methods."""
        prc = ConfigParser.RawConfigParser()
        prc.read('defConfig.ini')
        actionMap = dict(prc.items('ACTIONMAP'))
        methName = actionMap[act]
        meth = getattr(methods, methName)
        return meth

    def processMeth(self, meth, args, resp):
        """Process defined method and form response.

        Could raise libvirtError while processing.
        """
        if meth.__name__ == 'create':
            res = meth(self.con, args)
        else:
            dom = self.defineDomain(args.get('name'), args.get('id'))
            res = meth(dom)

        resp.body = simplejson.dumps({'result': res, 'error': None})
        return resp

    def handleError(self, req, resp, err):
        """Process occured errors and form response in this cases."""
        resp.status = 400
        resp.body = simplejson.dumps({'result': 'Fault',
                                      'error': err.get_error_code(),
                                      'message': err.message})
        logger = logging.getLogger('manageVM.server')
        logger.error('Error occured from host ' + req.client_addr
                          + ' ' + err.message)
        return resp


def main():
    app = ManageVM()
    srvr = make_server('', 8080, app)
    logger = logging.getLogger('manageVM')
    logger = confLogging.configLog(logger)
    try:
        srvr.serve_forever()
    except KeyboardInterrupt:
        logger.error('Stop serving due to keyboard interrupt')


if __name__ == '__main__':
    main()
