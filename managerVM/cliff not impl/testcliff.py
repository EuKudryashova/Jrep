import argparse
import sys
import simplejson
import logging
import cliff
from webob import Request
from cliff.app import App
from cliff.lister import Lister
from cliff.commandmanager import CommandManager
import confLogging


class resLister(Lister):

    def take_action(self, parsed_args):
        if parsed_args['Error'] != None:
            columns = parsed_args.keys()
            data = parsed_args.values()
            return (columns, data)
        columns = parsed_args['result'][0].keys()
        data = parsed_args['result'].values()
        return(columns, data)
        

class ClientApp(App):
    def __init__(self):
        super(ClientApp, self).__init__(description='client app',
                                      version='0.1',
                                      command_manager=CommandManager('client.app'))

    def build_option_parser(self, description, version):
        parser = argparse.ArgumentParser(description='Here must be help')
        parser.add_argument('-a', '--action', dest='action', type=str,
                            choices=['crt', 'del', 'on', 'off', 'reb',
                                     'state', 'sh_os', 'sh_vm'],
                            required=True, help='Choise action ')
        parser.add_argument('-i', dest='id', help='ID of specified VM')
        parser.add_argument('-n', dest='name', help='Name of specified VM')
        parser.add_argument('-o', dest='os', help='OS for new vm')
        return parser

    def parse_result(self, res):
        res = res.replace(',', '').split()
        print res
        parser = argparse.ArgumentParser()
        parser.add_argument('-r', dest='Result', required=True)
        parser.add_argument('-v', dest='VM')
        parser.add_argument('-s', dest='State')
        parser.add_argument('-o', dest='OS')
        parser.add_argument('-e', dest='Error')
        parser.add_argument('-i', dest='ID_OS')
        parser.add_argument('-m', dest='Message')
        return parser.parse_args(res)
        
    
    def configure_logging(self):
        self.logger = logging.getLogger('manageVM.client')
        self.logger = confLogging.configLog(self.logger)

    def form_request(self, usrConfig):
        req = Request.blank('http://localhost:8080')
        req.content_type = 'application/json'
        req.body = simplejson.dumps(usrConfig)
        return req

    def clean_up(self, res):
        #self.logger.info(res['result'])
        lister = resLister(self, res)
        res = self.parse_result(res)
        lister.run(res)
        print (res['result']) #change !!!
        if res['error'] != None:
            self.logger.error(res['message'])
            print ('error')

    def run(self, argv):
        self.configure_logging()
        arglist = self.parser.parse_args(argv)
        args = vars(arglist)
        req = self.form_request(args)
        resp = req.get_response()
        self.clean_up(resp.body)

def main(argv):
    app = ClientApp()
    app.run(argv)

    
if __name__ == '__main__':
    main(sys.argv[1:])
