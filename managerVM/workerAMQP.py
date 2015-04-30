import threading

__author__ = 'kudryashova'
import pika
import logging
import uuid
import ConfigParser
import simplejson
import manageBridges
import methods
import pdb

logging.getLogger('pika').setLevel(logging.ERROR)


class Worker(object):

    def __init__(self):

        self.con = pika.BlockingConnection(pika.ConnectionParameters(
                                           'localhost'))
        self.channel = self.con.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue

    def define_queue(self, q_name):
        self.channel.queue_declare(queue=q_name)

    def send_mes(self, json, reply_to):
        try:
            action = json['action']
        except KeyError as err:
            res = self.handleError(err)
            return res
        queue = self.get_queue(action)
        body = simplejson.dumps(json)
        print 'send     ' + body
        self.corr_id = str(uuid.uuid4())
        #pdb.set_trace()
        self.channel.basic_publish(exchange='',
                                   properties=pika.BasicProperties(
                                   content_type='application/json',
                                   reply_to=reply_to),
                                   routing_key=queue,
                                   body=body)
        self.response = None

        while self.response is None:
            self.con.process_data_events()
        print '\n\n\n\n\n\n\n\n' + self.response + '\n\n\n\n\n\n\n\n\n\n'
        return self.response

    def process_mes(self, ch, method, props, body):   # received mess
        #pdb.set_trace()
        try:
            json = simplejson.loads(body)
            meth = self.defineMethod(json['action'])
            json = self.processMeth(meth, json)
            res = json
        except Exception as err:
            err_json = self.handleError(err)
            res = err_json
        self.log_result(res)
        res = simplejson.dumps(res)
        print res
        self.channel.basic_publish(exchange='',
                                   properties=pika.BasicProperties(
                                   content_type='application/json'),
                                   routing_key=props.reply_to,
                                   body=res)

    def receive_res(self, ch=None, method=None, props=None, body = None):
        self.response = body

    def defineMethod(self, act):
        """Define required method, get it from module with allowed methods."""
        prc = ConfigParser.RawConfigParser()
        prc.read('defConfig.ini')
        actionMap = dict(prc.items('ACTIONMAP'))
        methName = actionMap[act]
        meth = getattr(methods, methName, None) or getattr(manageBridges, methName, None)
        return meth

    def get_queue(self, action):
        prc = ConfigParser.RawConfigParser()
        prc.read('defConfig.ini')
        queues = dict(prc.items('ACTIONQUEUEMAP'))
        queue = queues[action]
        return queue

    def processMeth(self, meth, args):
        res = meth(**args)
        json = {'result': res, 'error': None}
        return json

    def start_consuming(self):
        t = threading.Thread(target=self.channel.start_consuming)
        t.daemon = True
        t.start()

    def do_basic_consume(self, meth, queue):
        t = threading.Thread(target=self.channel.basic_consume, args=(meth, ), kwargs={'no_ack': True, 'queue': queue})
        t.daemon = True
        t.start()

    def handleError(self, err):
        """Process occured errors and form response in this cases."""
        res = {'result': 'Fault', 'error': err.message}
        return res

    def log_result(self, res):
        if res['error']:
            self.logger.error(res['error'])
            return
        self.logger.info(res['result'])
        pass

    def stop(self):
        # undefine queues
        # close connection etc.
        pass