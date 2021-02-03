"""
Config for working with Elasticsearch
"""

conf = {}
conf['elasticsearch'] = {}
conf['elasticsearch']['host'] = '10.225.227.134'#'elastic1.rc.int.colorado.edu'
conf['elasticsearch']['port'] = 9200
conf['elasticsearch']['use_ssl'] = True
conf['elasticsearch']['verify_certificates'] = False
conf['elasticsearch']['credentials'] = {}
conf['elasticsearch']['credentials']['username'] = ''
conf['elasticsearch']['credentials']['password'] = ''
