# -*- coding: utf-8 -*-

import json

import psycopg2
import pymongo


class JsonWPipeline(object):

    def open_spider(self, spider):
        self.file = open('output.jl', 'w')

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        dict_item = dict(item)
        dict_item.pop('_internal_id', None)  # internal_id required only for SQL DB storages
        line = json.dumps(dict_item) + "\n"
        self.file.write(line)
        return item


class MongoPipeline(object):

    collection_name = 'scrapy_items'

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DATABASE', 'items')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        dict_item = dict(item)
        dict_item.pop('_internal_id', None)  # internal_id required only for SQL DB storages
        self.db[self.collection_name].insert_one(dict_item)
        return item


class PostgreSQLPipeline(object):

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings.get('SQL_DB_SETUP', {}))

    def __init__(self, db_conf):
        self.db_conf = db_conf

    def open_spider(self, spider):
        self.connection = psycopg2.connect(**self.db_conf)
        self.connection.autocommit = True

    def close_spider(self, spider):
        self.connection.close()

    def process_item(self, item, spider):
        query = "insert into companies(company_id,name, phone, category, address, city) values (%s,%s,%s,%s,%s,%s)"
        reviews_tuple = (
            (item['_internal_id'], r['rating'], r['review'], r['date']) for r in item.get('reviews', [])
        )

        with self.connection.cursor() as curs:
            curs.execute(
                query,
                list(map(item.get, ('_internal_id', 'name', 'phone', 'category', 'address', 'city')))
            )
            curs.executemany(
                """INSERT INTO reviews(company_id, rating, review, date) VALUES (%s, %s, %s, %s)""",
                reviews_tuple
            )
        return item


class DbPipeline(object):
    @classmethod
    def from_crawler(cls, crawler):
        if crawler.settings.get('MONGO_URI'):
            return MongoPipeline.from_crawler(crawler)
        elif crawler.settings.get('SQL_DB_SETUP'):
            return PostgreSQLPipeline.from_crawler(crawler)
        else:
            return JsonWPipeline()
