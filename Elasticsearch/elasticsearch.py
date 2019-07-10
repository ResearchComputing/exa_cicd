"""
Utilities for interacting with Elasticsearch
"""

from config import conf

import elasticsearch

def get_elasticsearch_client(conf):
    """Returns an Elasticsearch client configured from a pipeline.config.Config."""

    conf_kwargs = dict(
        hosts=[{'host': conf.elasticsearch.host, 'port': conf.elasticsearch.port}],
        use_ssl=conf.elasticsearch.use_ssl,
        verify_certs=conf.elasticsearch.verify_certificates,
        connection_class=elasticsearch.RequestsHttpConnection
    )

    if conf.elasticsearch.credentials.username:
        credentials = (
            conf.elasticsearch.credentials.username,
            conf.elasticsearch.credentials.password,
        )
        conf_kwargs.update(dict(http_auth=credentials))

    elasticsearch_client = elasticsearch.Elasticsearch(**conf_kwargs)

    return elasticsearch_client



def scroll_query(elasticsearch_client, query_args):
    """
    Convenience function for scrolling through elasticsearch queries.

    Takes a configured elasticsearch client, and a dictionary of kwargs to be forwarded search().
    The query will be executed with a default scroll size of 100. An iterator of results `_source`
    contents will be returned.
    """

    if 'size' not in query_args:
        query_args['size'] = 100
    if 'scroll' not in query_args:
        query_args['scroll'] = '10m'

    try:
        results = elasticsearch_client.search(**query_args)
        scroll_id = results['_scroll_id']
        hit_count = len(results['hits']['hits'])
    except elasticsearch.NotFoundError:
        hit_count = 0

    while hit_count > 0:
        for document in results['hits']['hits']:
            yield document['_source']
        results = elasticsearch_client.scroll(scroll_id=scroll_id, scroll=query_args['scroll'])
        hit_count = len(results['hits']['hits'])
