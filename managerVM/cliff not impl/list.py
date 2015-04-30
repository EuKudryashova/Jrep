import logging

from cliff.lister import Lister

import main


class resLister(Lister):

    logger = logging.getLogger('manageVM.client')

    def get_parser(self, prog_name):# ?? look where defined
        parser = super(resLister, self).get_parser(prog_name)
        parser.add_argument('-s', dest='show', choises=['os', 'vm'],
                            help='Define list to show')
        return parser

    def take_action(self, parsed_args):
        if parsed_args.show == 'os':
            usrConfig = {'action': 'sh_os'}
        if parsed_args.show == 'vm':
            usrConfig = {'action': 'sh_vm'}
        res = main.process_request(usrConfig) 
        self.logger.info('smth')    # change
        columns = res['Result'].keys()
        data = res['Result'].values()
        return (columns, data)
