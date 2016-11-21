from flask import Flask, request, logging
from logging.handlers import RotatingFileHandler
import csv
from collections import namedtuple, OrderedDict
import sys
import os
from tqdm import tqdm
import numpy as np
import time
import json
import ipaddress


class ip2location_database:

    db = OrderedDict()
    db_keys = None
    ## IN THE ROW BELOW THE '_id' FIELD IS OMITTED BECAUSE NAMED TUPLES CANNOT HAVE FIELDS THAT BEGIN WITH AN UNDERSCORE
    ip2location_db_row = namedtuple('ip2location_db_row','ip_from ip_to country_code country_name region_name city_name latitude longitude zip_code time_zone')
    database_flatfile_path = None
    abs_min = None
    abs_max = None    

    def __init__(self, db_name="/opt/IP2LocationService/IP2LOCATION-LITE-DB11.CSV"):
        self.database_flatfile_path = db_name
        print self.database_flatfile_path

    def read_database(self):
        try:
            first_line = True
            with open(self.database_flatfile_path, "rb") as fin:
                reader = csv.reader(fin)
                for row in tqdm(reader):
                    self.db[int(row[1])] = self.ip2location_db_row(ip_from=int(row[0]), ip_to=int(row[1]), country_code=str(row[2]), country_name=str(row[3]), region_name=str(row[4]), city_name=str(row[5]), latitude=float(row[6]), longitude=float(row[7]), zip_code=str(row[8]), time_zone=str(row[9]))
                    if first_line:
                        first_line = False
                        self.abs_min = int(row[0])
            self.db_keys = np.array(self.db.keys())
            self.abs_max = int(self.db_keys[-1])
        except:
            print "Failed to read database. Please make sure that file exists and has a schema matching the one found at http://lite.ip2location.com/database/ip-country-region-city-latitude-longitude-zipcode-timezone"
            print sys.exc_info()[0]
            raise
    
    def set_database_path(self, db_name):
        self.database_flatfile_path = db_name

    def find_one_ip(self, ip_address_to_query="172.217.3.206"):
        if '.' in ip_address_to_query:
            ip_address_to_query = int(ipaddress.IPv4Address(unicode(ip_address_to_query)))
        else:
            ip_address_to_query = int(ip_address_to_query)

        if ip_address_to_query < self.abs_min:
            return "UNDEFINED"
        elif ip_address_to_query > self.abs_max:
            return "UNDEFINED"
        else:
            low = 0
            mid = len(self.db)/2
            high = len(self.db)
            iterations = 0
            while True: 
                iterations += 1
                if ip_address_to_query > self.db_keys[mid]:
                    low = mid
                    mid = ((high - mid)/2) + mid
                elif ip_address_to_query >= self.db[self.db_keys[mid]].ip_from:
                    print iterations
                    return self.db[self.db_keys[mid]]
                else:
                    high = mid
                    mid = mid - ((mid - low)/2)

    def find_many_ips(self, ip_addresses_to_query=["172.217.3.206"]):
        min_curr = self.abs_min
        min_index = 0
        ip_num_to_ip_map={}
        results = {}
        for i in xrange(len(ip_addresses_to_query)):
            if '.' in ip_addresses_to_query[i]:
                ip_num = int(ipaddress.IPv4Address(unicode(ip_addresses_to_query[i])))
                ip_num_to_ip_map[ip_num] = ip_addresses_to_query[i] 
                ip_addresses_to_query[i] = ip_num
        ip_addresses_to_query.sort()
        for item in self.db_keys:
            for i in xrange(min_index, len(ip_addresses_to_query)):
                if (ip_addresses_to_query[i] <= item) and (ip_addresses_to_query[i] >= min_curr):
                    results[ip_addresses_to_query[i]] = self.db[item]
                else:
                    min_index = i
                    break
        return {ip_num_to_ip_map[results.keys()[i]]:results[results.keys()[i]] for i in xrange(len(results))}

def daemonize():
    """
    do the UNIX double-fork magic, see Stevens' "Advanced
    Programming in the UNIX Environment" for details (ISBN 0201563177)
    http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
    """
    stdin = "/dev/null"
    stdout = "/dev/null"
    stderr = "/dev/null"
    try:
            pid = os.fork()
            if pid > 0:
                    # exit first parent
                    sys.exit(0)
    except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

    # decouple from parent environment
    os.chdir("/")
    os.setsid()
    os.umask(0)

    # do second fork
    try:
            pid = os.fork()
            if pid > 0:
                    # exit from second parent
                    sys.exit(0)
    except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

    # redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    # write pidfile
    # atexit.register(self.delpid)
    # pid = str(os.getpid())
    # file(self.pidfile,'w+').write("%s\n" % pid)

app = Flask(__name__)
db = ip2location_database()

@app.route("/lookup/", methods=['POST'])
def find_ip():
    result = {}
    args = request.get_json(force=True)
    result['type'] = "success"
    result['result'] = db.find_one_ip(args['ip'])._asdict()
    result['result']['_id'] = "" #this must be added here as namedtuples do not support fields with '_' in their name
    return json.dumps(result)

@app.route("/ip2location/getcoor/<ip>", methods=['GET'])
def emulate_reddys_service(ip):
    result = {}
    try:
        result['type'] = "success"
        result['result'] = db.find_one_ip(ip)._asdict()
        result['result']['_id'] = "" #this must be added here as namedtuples do not support fields with '_' in their name
        return json.dumps(result)
    except:
        result['type'] = "error"
        result['result'] = None
        return json.dumps(result)

if __name__ == "__main__":
    daemonize()
    db.read_database()
    logger = logging.getLogger('werkzeug')
    handler = RotatingFileHandler('access.log', maxBytes=500)
    logger.addHandler(handler)
    app.run(host='0.0.0.0', port=5000)
