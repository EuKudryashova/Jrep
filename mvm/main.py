from webob import Request
import simplejson


def process_request(self, usrConfig):# share how?
    req = Request.blank('http://localhost:8080')
    req.content_type = 'application/json'
    req.body = simplejson.dumps(usrConfig)
    resp = req.get_response()
    res = simplejson.loads(resp.body)
    return res


class ClientApp(App):
    def __init__(self):#zbs
        super(ClientApp, self).__init__(description='client app',
                                      version='0.1',
                                      command_manager=CommandManager('client.app'))

    def build_option_parser(self, description, version):# ????
        parser = argparse.ArgumentParser(description='Here must be help')
        return parser

    def configure_logging(self):# hz
        self.logger = logging.getLogger('manageVM.client')
        self.logger = confLogging.configLog(self.logger)


def main(argv):
    app = ClientApp()
    app.run(argv)


if __name__ == '__main__':
    main(sys.argv[1:])
