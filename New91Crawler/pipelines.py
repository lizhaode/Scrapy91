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

from New91Crawler.items import DownloadVideoItem, SaveMovieInfoItem, MyFollowMovieInfoItem
from New91Crawler.lib.RandomIP import x_forwarded_for


class DownloadVideoPipeline(FilesPipeline):
    def get_media_requests(self, item, info):
        if isinstance(item, DownloadVideoItem):
            info.spider.logger.warn('接到下载任务，文件名：{0}\n地址：{1}\n'.format(item['file_name'] + '.mp4', item['file_urls']))
            customer_headers = {
                'User-Agent': random.choice(info.spider.settings.get('USER_AGENT')),
                'X-Forwarded-For': x_forwarded_for()
            }
            return scrapy.Request(url=item['file_urls'], meta=item,headers=customer_headers)

    def file_path(self, request, response=None, info=None):
        down_name = request.meta['file_name'] + '.mp4'
        return down_name


class SaveMoviePipeline:
    def process_item(self, item, spider):
        if isinstance(item, SaveMovieInfoItem):
            file_name = '第{0}页.json'.format(item['page_number'])
            name_and_link = json.dumps(item['movie_name_and_link'], ensure_ascii=False)
            if os.path.exists('info') is False:
                os.mkdir('info')
            with open('info/{0}'.format(file_name), 'w') as f:
                f.write(name_and_link)
            spider.logger.warn('保存{0}完毕'.format(file_name))
            return item
        else:
            return item


class SaveMyFollowPipeline:
    def process_item(self, item, spider):
        if isinstance(item, MyFollowMovieInfoItem):
            if os.path.exists('myfollowinfo') is False:
                os.mkdir('myfollowinfo')
            with open('myfollowinfo/follow.json', 'w') as f:
                f.write(json.dumps(item['movie_name_and_page'], ensure_ascii=False))
            spider.logger.warn('保存我的关注视频信息完毕')
            return item
