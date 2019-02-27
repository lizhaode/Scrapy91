# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import json
import os
import random

import scrapy
from scrapy.pipelines.files import FilesPipeline

from New91Crawler.items import DownloadVideoItem, SaveMovieInfoItem, UpdateMovieLinkItem
from New91Crawler.lib.RandomIP import x_forwarded_for
from New91Crawler.lib.Database import Sql


class DownloadVideoPipeline(FilesPipeline):
    def __init__(self, store_uri, download_func=None, settings=None):
        super().__init__(store_uri, download_func=None, settings=None)
        self._open_mysql_record = settings.getbool('MYSQL_RECORD_ENABLE')
        self._host = settings.get('MYSQL_HOST')
        self._port = settings.getint('MYSQL_PORT')
        self._user = settings.get('MYSQL_USER')
        self._password = settings.get('MYSQL_PASSWORD')
        self._database = settings.get('MYSQL_DATABASE')

    def open_spider(self, spider):
        self.spiderinfo = self.SpiderInfo(spider)
        if self._open_mysql_record:
            self._sql = Sql(database=self._database, host=self._host, port=self._port, user=self._user,
                            password=self._password)
        else:
            self._sql = None

    def close_spider(self, spider):
        if self._sql:
            self._sql.close_connect()

    def get_media_requests(self, item, info):
        if isinstance(item, DownloadVideoItem):
            info.spider.logger.warn('接到下载任务，文件名：{0}\n地址：{1}\n'.format(item['file_name'] + '.mp4', item['file_urls']))
            customer_headers = {
                'User-Agent': random.choice(info.spider.settings.get('USER_AGENT')),
                'X-Forwarded-For': x_forwarded_for()
            }
            return scrapy.Request(url=item['file_urls'], meta=item, headers=customer_headers)

    def file_path(self, request, response=None, info=None):
        down_name = request.meta['file_name'] + '.mp4'
        return down_name

    def item_completed(self, results, item, info):
        if isinstance(item, dict) or self.files_result_field in item.fields:
            item[self.files_result_field] = [x for ok, x in results if ok]
            for ok, x in results:
                if ok and self._sql:
                    update_sentence = "UPDATE `my_follow` SET `is_download` = 1 WHERE `real_link` = '{0}'".format(
                        x['url'])
                    self._sql.update_or_insert_sql(update_sentence)
        return item


class SaveMoviePipeline:

    def __init__(self, open_mysql_record, host, port, user, password, database):
        self._open_mysql_record = open_mysql_record
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database

    @classmethod
    def from_crawler(cls, crawler):
        open_mysql_record = crawler.settings.getbool('MYSQL_RECORD_ENABLE')
        host = crawler.settings.get('MYSQL_HOST')
        port = crawler.settings.getint('MYSQL_PORT')
        user = crawler.settings.get('MYSQL_USER')
        password = crawler.settings.get('MYSQL_PASSWORD')
        database = crawler.settings.get('MYSQL_DATABASE')

        return cls(open_mysql_record, host, port, user, password, database)

    def open_spider(self, spider):
        if self._open_mysql_record:
            self._sql = Sql(database=self._database, host=self._host, port=self._port, user=self._user,
                            password=self._password)
        else:
            self._sql = None

    def close_spider(self, spider):
        if self._sql:
            self._sql.close_connect()

    def process_item(self, item, spider):
        if isinstance(item, SaveMovieInfoItem):
            file_name = '第{0}页.json'.format(item['page_number'])
            link_and_name = json.dumps(item['movie_link_and_name'], ensure_ascii=False)
            if not item['movie_link_and_name']:
                return item
            elif os.path.exists('info') is False:
                os.mkdir('info')
            with open('info/{0}'.format(file_name), 'w') as f:
                f.write(link_and_name)
            # 写入 MySQL
            if self._sql:
                for k, v in item['movie_link_and_name'].items():
                    insert_sentence = "INSERT INTO `my_follow` (`video_name`,`video_url`,`page_name`) VALUES ('{0}','{1}','{2}')".format(
                        v, k, file_name.split('.')[0])
                    self._sql.update_or_insert_sql(insert_sentence)

            spider.logger.warn('保存{0}完毕'.format(file_name))
            return item
        else:
            return item


class UpdateMoviePipeline:
    def __init__(self, open_mysql_record, host, port, user, password, database):
        self._open_mysql_record = open_mysql_record
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database

    @classmethod
    def from_crawler(cls, crawler):
        open_mysql_record = crawler.settings.getbool('MYSQL_RECORD_ENABLE')
        host = crawler.settings.get('MYSQL_HOST')
        port = crawler.settings.getint('MYSQL_PORT')
        user = crawler.settings.get('MYSQL_USER')
        password = crawler.settings.get('MYSQL_PASSWORD')
        database = crawler.settings.get('MYSQL_DATABASE')

        return cls(open_mysql_record, host, port, user, password, database)

    def open_spider(self, spider):
        if self._open_mysql_record:
            self._sql = Sql(database=self._database, host=self._host, port=self._port, user=self._user,
                            password=self._password)
        else:
            self._sql = None

    def close_spider(self, spider):
        if self._sql:
            self._sql.close_connect()

    def process_item(self, item, spider):
        if isinstance(item, UpdateMovieLinkItem):
            if self._sql:
                update_sentence = "UPDATE `my_follow` SET `real_link`='{0}' WHERE `video_url`='{1}'".format(
                    item['movie_real_url'], item['movie_page_url'])
                self._sql.update_or_insert_sql(update_sentence)
            spider.logger.warn('更新数据库完毕')
            return item
        else:
            return item
