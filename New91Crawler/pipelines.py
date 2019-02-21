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

from New91Crawler.items import DownloadVideoItem, SaveMovieInfoItem
from New91Crawler.lib.RandomIP import x_forwarded_for


class DownloadVideoPipeline(FilesPipeline):
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


class SaveMoviePipeline:
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
            spider.logger.warn('保存{0}完毕'.format(file_name))
            return item
        else:
            return item
