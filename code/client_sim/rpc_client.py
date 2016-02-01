#!/bin/python


#################################################################################################################
# Author: Gueyoung Jung
# Contact: gjung@research.att.com
# Version 2.0.1: Dec. 1, 2015
#
#################################################################################################################


import xmlrpclib
import json
import sys, time


class RPCInterface:

    def __init__(self, _host_ip):
        self.proxy = xmlrpclib.ServerProxy(_host_ip)

    def place_app(self, _app):
        return self.proxy.place_app(_app)

    def print_tester(self):
        return self.proxy.print_tester()

    def test_place_app(self, _dir_file):
        return self.proxy.place_app_file(_dir_file)



# Unit test
if __name__ == '__main__':
    rpc = RPCInterface("http://localhost:8002/")

    #print rpc.print_tester()
    
    time.sleep(10)
    app_data = open("./test_app_inputs/affinity.json", 'r')
    print rpc.place_app(app_data.read())
    
    time.sleep(10)
    app_data = open("./test_app_inputs/io_affinity.json", 'r')
    print rpc.place_app(app_data.read())
    
