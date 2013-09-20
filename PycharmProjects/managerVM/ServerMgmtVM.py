"""
Module make server to manage VMs,  ...
"""
import logging
import simplejson
from wsgiref.simple_server import make_server
import libvirt
import webob
from sqlalchemy import *
import workerAMQP
import methods
import confLogging
import DB
import queries
import manageBridges


class ManageVM(workerAMQP.Worker):
    """Application for serving.

    Allows manipulations of VM's images, such as creating, destroying,
    changing status of given VM.
    """

    def __init__(self, con):
        """Initialise serving application."""
        self.con = libvirt.open(con)
        self.logger = logging.getLogger('manageVM.server')
        super(ManageVM, self).__init__()

    def __call__(self, environ, start_response):
        """Loads  given request, process it and return response"""
        req = webob.Request(environ)
        resp = self.processReq(req)
        return resp(environ, start_response)

    def processReq(self, req):
        """Processing given request. Send Query to specified worker"""
        json = simplejson.loads(req.body)
        resp = webob.Response(status=200, content_type='application/json')
        resp.body = self.send_mes(json)
        return resp

    def run(self):
        self.define_queue('s_vm')
        self.define_queue('s_net')
        self.define_queue('vm_s')
        self.define_queue('net_s')
        self.do_basic_consume(self.receive_res, 'vm_s')
        self.do_basic_consume(self.receive_res, 'net_s')
        self.start_consuming()


def main():
    app = ManageVM("qemu:///system")
    srvr = make_server('', 8080, app)
    engine = create_engine('mysql://root:password@localhost/VM_db', echo=True)
    DB.Base.metadata.create_all(engine)
    logger = logging.getLogger('manageVM')
    logger = confLogging.configLog(logger)
    app.run()
    methods.set_worker()
    manageBridges.set_worker()
    try:
        srvr.serve_forever()
    except KeyboardInterrupt:
        session = queries.getSession()
        session.close()
        app.stop()
        logger.error('Stop serving due to keyboard interrupt')


if __name__ == '__main__':
    main()