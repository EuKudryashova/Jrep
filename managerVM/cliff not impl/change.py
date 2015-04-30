import logging

from cliff.show import ShowOne

import main


class Manager(ShowOne):

    logger = logging.getLogger('manageVM.client')
    
    def get_parser(self, prog_name):# ?? look where defined
        parser = super(resLister, self).get_parser(prog_name)
        parser.add_argument('-a', '--action', dest='action', type=str,
                            choices=['crt', 'del', 'on', 'off', 'reb',
                                     'state'], required=True,
                            help='Choise action ')
        parser.add_argument('-i', dest='id', help='ID of specified VM')
        parser.add_argument('-n', dest='name', help='Name of specified VM')
        parser.add_argument('-o', dest='os', help='OS for new vm')
        return parser

    def take_action(self, parsed_args):
        args = vars(parsed_args)
        res = main.process_request(args)
        if res['Error']:
            self.logger.warning('error occured')
        else:
            self.logger.info('smth') # change
        columns = ('Result', 'Error')
        data = res.values()
        return(columns, data)
