import argparse
import datetime
from dictdiffer import diff
from elasticsearch import Elasticsearch
import functools
import logging
import os
import sys
import time
from urllib.parse import urlparse
try:
       import simplejson as json
except ImportError:
       import json

logging.basicConfig(stream=sys.stdout,level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger = logging.getLogger('[query_es]')


def differ(doc1, doc2, ignore_set=[]):
        result = list(diff(doc1, doc2, ignore=ignore_set))

        for entry in result:
                if len(entry[2]) == 1:
                        print('\n\t %s :\n\t\t %s\t%s' % entry)
                else:
                        print('\n\t %s :\n\t\t %s\n\t\t\t%s\n\t\t\t%s' %
                              (entry[0], entry[1], entry[2][0], entry[2][1]))
        return(len(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--url"      , required=True , default='', type=str, help="Elasticsearch endpoint")
    parser.add_argument("--port"     , required=True , default='', type=int, help="Elasticsearch port")
    parser.add_argument("--username" , required=True , default='', type=str, help="Elasticsearch username")
    parser.add_argument("--password" , required=True , default='', type=str, help="Elasticsearch password")
    parser.add_argument("--index"    , required=True , default='', type=str, help="Elasticsearch index")
    parser.add_argument("--request"  , required=True , default='', type=str, help="Elasticsearch request")
    parser.add_argument("--ca_certs" , required=False,  default='', type=str, help="CA cert")
    parser.add_argument("--verify_certs"  , required=False,  action='store_true', help="CA cert verification")
    parser.add_argument("--output_file"  ,required=True, type=str, help="json output file")
    parser.add_argument("--ref_file"  ,required=True, type=str, help="reference file")
    parser.add_argument("--force"  , required=False, action='store_true', help="Force overwrite of output file")
    
    args = {}

    for arg, value in vars(parser.parse_args()).items():
        if arg != 'password':
            args[arg] = value

    password = parser.parse_args().password
    logger.info(functools.reduce(lambda x,y:  '%s \n\t --%s=%s' % (x,y[0],y[1]), args.items(), "Arguments: " ))

    if args['verify_certs'] == True and args['ca_certs'] == '':
        raise Exception("Please specify CA certificate or run with --verify_certs=False")

    if os.path.isfile(args['output_file']) == True and args['force'] == False :
        raise IOError("The output file %s does exist. In order to overwrite it use --force=True" %args['output_file'])

    e = urlparse(args['url'])
    logger.info("Connecting to " + e.hostname)
    es=Elasticsearch([{"host":e.hostname,"http_auth":args['username']+":"+password,"port":args['port']}],
                        #use_ssl=True,
                        #verify_certs=args['verify_certs'],
                        #ca_certs=args['ca_certs']
                        )
    logger.info('Cluster health state: %s' % es.cluster.health())

    logger.info('List of indices:\n %s' % es.indices.get_alias("*"))
    logger.info('Getting results from ES')
    request = json.loads(open(args['request'],"r").read())
    res = es.search(index=args['index'],body=request)

    data = res['hits']['hits'][0]['_source']['message']

    logger.info('Saving to ' + args['output_file'])
    with open(args['output_file'],'w') as write_json:
        write_json.write(json.dumps(data))

    with open(args['ref_file']) as read_json:
        ref_json = json.loads(read_json.read())

    differ_out = differ(ref_json, data, ignore_set=['_id', '_timestamp', '_timestamp_end'])

    if differ_out == 0:
        print("\n@@@@@ SUCCESS @@@@@\n all the attributes saved correctly")
    else:
        print("\n@@@@@ FAILURE @@@@@\n")
    exit(differ_out)