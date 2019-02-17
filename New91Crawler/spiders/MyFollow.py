import json
import time

import scrapy
from scrapy.http import HtmlResponse

from New91Crawler.items import MyFollowMovieInfoItem, DownloadVideoItem


class MyFollowSpider(scrapy.Spider):
    name = 'MyFollow'
    cookie = ''

    def start_requests(self):
        me_main_url = 'http://91porn.com/my_subs.php'
        login_headers = {
            'Cookie': self.cookie,
            'Referer': 'http://91porn.com/index.php'
        }

        yield scrapy.Request(url=me_main_url, callback=self.parse_me, headers=login_headers)

    def parse_me(self, response: HtmlResponse):
        # 兼容 cookie 失效只想下载 json 文件内容的情况
        if 'login.php' in response.url:
            self.logger.warn('cookie失效，直接用follow.json下载')
            with open('myfollowinfo/follow.json') as f:
                movie_info = json.loads(f.read())
            self.logger.warn('文件中保存了{0}个视频'.format(len(movie_info)))
            for link, title in movie_info.items():
                yield scrapy.Request(url=link, callback=self.parse_my_follow_real_link)
        else:
            myvideo_list = response.css('div.maindescwithoutborder')
            video_info_list = myvideo_list.css('a')
            self.logger.warn('解析{0}成功，存在{1}个视频'.format(response.url, len(video_info_list)))
            # 将解析到的视频放到内存中，减少硬盘读写
            title_and_link_dict = {}
            for item in video_info_list:
                title = item.css('::text').extract_first()
                link = item.css('a::attr(href)').extract_first()
                # 不知道为啥有时候会出现 email protected
                if 'email protected' in title:
                    continue
                title_and_link_dict[link] = title
            self.logger.warn('最终解析{0}个视频'.format(len(title_and_link_dict)))

            # 拼装 meta 内容
            meta_info = {}
            movie_info = response.meta.get('movie_info')
            if movie_info is not None:
                movie_info.update(title_and_link_dict)
                meta_info['movie_info'] = movie_info.copy()
            else:
                meta_info['movie_info'] = title_and_link_dict

            self.logger.warn('解析完毕，检查是否存在下一页'.format(response.url))
            next_page_tag = response.css('a[href*="?&page="]')
            next_link = ''
            for i in next_page_tag:
                if '»' == i.css('a::text').extract_first():
                    ori_link = i.css('a::attr(href)').extract_first()
                    next_link = response.urljoin(ori_link)
                    self.logger.warn('存在下一页')
                    next_headers = {
                        'Cookie': self.cookie,
                        'Referer': response.url
                    }
                    yield scrapy.Request(url=next_link, callback=self.parse_me, headers=next_headers, meta=meta_info)

            if not next_link:
                self.logger.warn('所有页面视频解析完毕，开始保存文件')
                yield MyFollowMovieInfoItem(movie_name_and_page=meta_info['movie_info'])
                # 确保文件保存完毕
                time.sleep(30)
                with open('myfollowinfo/follow.json') as f:
                    movie_info = json.loads(f.read())
                self.logger.warn('文件中保存了{0}个视频'.format(len(movie_info)))
                for link, title in movie_info.items():
                    yield scrapy.Request(url=link, callback=self.parse_my_follow_real_link)

    def parse_my_follow_real_link(self, response: HtmlResponse):
        self.logger.warn('开始解析{0}真实视频'.format(response.url))
        title = response.css('#viewvideo-title::text').extract_first().strip()
        author = response.css('a[href*="uprofile.php"]').css('span::text').extract_first().strip()
        # 由于有的视频名字中带 / 会导致创建成文件夹，所以需要处理一下
        if '/' in title:
            title = title.replace('/', '')

        video_link = response.css('source::attr(src)').extract_first()
        if video_link:
            # 处理一下链接中 http://185.38.13.130//mp43/2998... 这种的 url
            video_link_list = video_link.split('//')
            real_video_link = video_link_list[0] + '//' + video_link_list[1] + '/' + video_link_list[2]
            self.logger.warn('视频:{0} 分析完毕,丢入下载 pipelines'.format(title))
            yield DownloadVideoItem(file_urls=real_video_link, file_name=title+'-'+author)
        else:
            self.logger.warn('获取视频下载地址失败，地址：{0}'.format(response.url))
