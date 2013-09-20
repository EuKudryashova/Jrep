import pdb
import types

__author__ = 'kudryashova'

import threading
import Queue
import logging
import simplejson
import uuid
import ConfigParser
import pika
import sys

logging.getLogger('pika').setLevel(logging.ERROR)


class Worker(object):
    def __init__(self):
        self.con = pika.BlockingConnection(pika.ConnectionParameters(
            'localhost'))
        self.channel = self.con.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.map_responses = {}
        self.available_methods = {}
        self.set_available_methods()

    def set_available_methods(self):
        """Set dictionary of available methods of current worker"""
        module = sys.modules[self.__module__]
        for el in dir(module):
            attr = getattr(module, el)
            if (isinstance(attr, types.MethodType) or
                    isinstance(attr, types.FunctionType)):
                self.available_methods[el] = attr
        print self.__module__ + '    ' + str(self.available_methods)

    def define_queue(self, q_name):
        """Define and bings to current channel specified queue"""
        self.channel.queue_declare(queue=q_name)

    def send_mes(self, json):
        """Sends message containing json to special queue, waits for result"""
        try:
            action = json['action']
        except KeyError as err:
            res = self.handleError(err)
            return res
        queue = self.get_queue(action)
        reply_to = self.get_reply_to_queue(queue)
        body = simplejson.dumps(json)
        corr_id = str(uuid.uuid4())
        self.map_responses[corr_id] = None
        self.channel.basic_publish(exchange='',
                                   properties=pika.BasicProperties(
                                       content_type='application/json',
                                       reply_to=reply_to,
                                       correlation_id=corr_id),
                                   routing_key=queue,
                                   body=body)
        while not self.map_responses[corr_id]:
            self.con.process_data_events()
        response = self.map_responses[corr_id]
        del self.map_responses[corr_id]
        return response

    def process_mes(self, ch, method, props, body):
        """Process request and forms response"""
        json = simplejson.loads(body)
        res = self.do_execute(json)
        self.log_result(res)
        res = simplejson.dumps(res)
        self.channel.basic_publish(exchange='',
                                   properties=pika.BasicProperties(
                                       content_type='application/json',
                                       correlation_id=props.correlation_id),
                                   routing_key=props.reply_to,
                                   body=res)

    def receive_res(self, ch=None, method=None, props=None, body=None):
        """Receive response and add it to map id-response"""
        self.map_responses[props.correlation_id] = body

    def execute_request(self, json, q):
        """Process defined in json action"""
        try:
            meth = self.defineMethod(json['action'])
            json = self.processMeth(meth, json)
            res = json
        except Exception as err:
            err_json = self.handleError(err)
            res = err_json
        q.put(res)

    def defineMethod(self, act):
        """Define required method, get it from module with allowed methods."""
        prc = ConfigParser.RawConfigParser()
        prc.read('defConfig.ini')
        actionMap = dict(prc.items('ACTIONMAP'))
        methName = actionMap[act]
        meth = self.available_methods[methName]
        return meth

    def get_queue(self, action):
        """Return queue binded to worker, which could process action"""
        prc = ConfigParser.RawConfigParser()
        prc.read('defConfig.ini')
        queues = dict(prc.items('ACTIONQUEUEMAP'))
        queue = queues[action]
        return queue

    def get_reply_to_queue(self, queue):
        """Return queue for replies, depended on request queue"""
        prc = ConfigParser.RawConfigParser()
        prc.read('defConfig.ini')
        replies = dict(prc.items('REPLYTOMAP'))
        reply = replies[queue]
        return reply

    def processMeth(self, meth, args):
        """Process method of worker"""
        del args['action']
        print args
        res = meth(**args)
        json = {'result': res, 'error': None}
        return json

    def start_consuming(self):
        """Make worker to start consuming for requests"""
        t = threading.Thread(target=self.channel.start_consuming)
        self.logger.info('start consuming')
        t.daemon = True
        t.start()

    def do_basic_consume(self, meth, queue):
        """Set queues to be listened"""
        t = threading.Thread(target=self.channel.basic_consume, args=(meth, ),
                             kwargs={'no_ack': True, 'queue': queue})
        self.logger.info('will consume queue: ' + queue)
        t.daemon = True
        t.start()

    def do_execute(self, json):
        """Define new thread to execute method"""
        q = Queue.Queue()
        t = threading.Thread(target=self.execute_request, args=(json, q))
        t.daemon = True
        t.start()
        result = q.get()
        return result

    def handleError(self, err):
        """Process occured errors and form response in this cases."""
        res = {'result': 'Fault', 'error': err.message}
        return res

    def log_result(self, res):
        """Make logging of given result"""
        if res['error']:
            self.logger.error(res['error'])
            return
        self.logger.info(res['result'])

    def stop(self):
        """Close connection to RabbitMQ server"""
        self.channel.stop_consuming()
        try:
            self.con.close()
        except Exception as err:
            self.logger.error('Close connection to RabbitMQ')
        self.logger.info('stop consuming, close connection to RabbitMQ')