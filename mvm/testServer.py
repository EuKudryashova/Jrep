from wsgiref.simple_server import make_server
import webob


httpd = make_server('', 8080, Clss)



httpd.serve_forever()


class Clss(object):
    def __init__():
        pass

    def __call__(self, environ, start_response):
        req = webob.Request(environ)
        resp = doReq(req)

        return resp

    def doReq(self, req):

        req->JSON

        ?import method ?

        res = method(*args)

        JSON->resp

        return resp


client: parse args, ->JSON -> req
                   ->    JSON ->res ->error

from webob request

form request
req.get_response()    !!!!


        
        
