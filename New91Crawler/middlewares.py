# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import random
import time

from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware
from scrapy.utils.response import response_status_message
from scrapy.utils.python import global_object_name

from New91Crawler.lib.RandomIP import x_forwarded_for


class CustomerUserAgentMiddleware(UserAgentMiddleware):

    def process_request(self, request, spider):
        if self.user_agent:
            request.headers.setdefault(b'User-Agent', random.choice(self.user_agent))
            request.headers.setdefault(b'X-Forwarded-For', x_forwarded_for())
            if 'view_video.php' in request.url and 'Referer' in request.headers:
                spider.logger.warn('为了匿名分析{0}，Referer去掉'.format(request.url))
                request.headers.pop('Referer')


class CustomerRetryMiddleware(RetryMiddleware):
    """
        去掉了一些判断，增加了 log
    """

    def process_response(self, request, response, spider):
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            spider.logger.warn('下载{0}中收到http错误code:{1}，丢入重试'.format(request.url, reason))
            spider.logger.warn('请求头:{0}'.format(request.headers))
            return self._retry(request, reason, spider) or response
        else:
            return response

    """
        去掉了 EXCEPTIONS_TO_RETRY 判断，无脑重试
    """

    def process_exception(self, request, exception, spider):
        spider.logger.warn('下载{0}中收到exception:{1}，丢入重试'.format(request.url, exception))
        spider.logger.warn('请求头:{0}'.format(request.headers))
        return self._retry(request, 'CustomerRetryError', spider)

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        retry_times = self.max_retry_times

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        if retries <= retry_times:
            time.sleep(3)
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust

            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value('retry/count')
            stats.inc_value('retry/reason_count/%s' % reason)
            return retryreq
        else:
            stats.inc_value('retry/max_reached')
            spider.logger.warn('{0}超过重试次数，停止重试'.format(request.url))
