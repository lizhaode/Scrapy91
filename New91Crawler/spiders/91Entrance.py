import scrapy
from scrapy.http.response.html import HtmlResponse

from New91Crawler.items import DownloadVideoItem, SaveMovieInfoItem


class Entrance(scrapy.Spider):
    name = '91Crawler'

    def start_requests(self):
        start_url = 'http://91porn.com/v.php?category=long&viewtype=basic'
        yield scrapy.Request(url=start_url, callback=self.parse)

    def parse(self, response: HtmlResponse):
        url_list = response.url.split('page=')
        if len(url_list) == 1:
            current_page_num = 1
        else:
            current_page_num = int(url_list[1])

        next_page_link = self.parse_next_link(response)
        filter_keywords = self.crawler.settings.getlist('FILTER_KEYWORDS')

        # 由于91视频页面太多，控制一下每次爬取的数量
        if current_page_num < 1 and next_page_link is not None:
            yield scrapy.Request(url=next_page_link, callback=self.parse)
        elif current_page_num <= 40 and next_page_link is not None:
            self.logger.warn('网页 {0} 获取完毕，开始解析'.format(response.url))
            # 获取当前页面的视频
            list_channel_list = response.css('div.listchannel')
            self.logger.warn('解析到{0}个视频页面'.format(len(list_channel_list)))

            link_and_title = {}
            for item in list_channel_list:
                a_tag = item.css('a')
                link = a_tag.css('a::attr(href)').extract_first()
                title = a_tag.css('a::attr(title)').extract_first()
                # 根据过滤关键字选择是否需要分析并下载
                if filter_keywords:
                    for filter_keyword in filter_keywords:
                        if filter_keyword in title:
                            link_and_title[link] = title
                            yield scrapy.Request(url=link, callback=self.parse_video_page)
                else:
                    link_and_title[link] = title
                    yield scrapy.Request(url=link, callback=self.parse_video_page)
            self.logger.warn('最终解析{0}个视频'.format(len(link_and_title)))
            yield SaveMovieInfoItem(page_number=current_page_num, movie_link_and_name=link_and_title)
            yield scrapy.Request(url=next_page_link, callback=self.parse)

    def parse_video_page(self, response: HtmlResponse):
        self.logger.warn('开始解析{0}真实视频'.format(response.url))
        title = response.css('#viewvideo-title::text').extract_first().strip()
        author = response.css('a[href*="uprofile.php"]').css('span::text').extract_first().strip()
        # 发现有的视频，名字相同，作者相同，只有Url中的viewkey不同
        view_key = response.url.split('viewkey=')[1].split('&')[0]
        # 由于有的视频名字中带 / 会导致创建成文件夹，所以需要处理一下
        if '/' in title:
            title = title.replace('/', '')

        video_link = response.css('source::attr(src)').extract_first()
        if video_link:
            # 处理一下链接中 http://185.38.13.130//mp43/2998... 这种的 url
            video_link_list = video_link.split('//')
            real_video_link = video_link_list[0] + '//' + video_link_list[1] + '/' + video_link_list[2]
            self.logger.warn('获取到下载链接，丢入下载 pipelines')
            down_file_name = title + '-' + author + '-' + view_key
            yield DownloadVideoItem(file_urls=real_video_link, file_name=down_file_name)
        else:
            self.logger.warn('获取视频下载地址失败，地址：{0}'.format(response.url))

    def parse_next_link(self, response: HtmlResponse) -> str:
        next_page_tag = response.css('a[href*="?category=long&viewtype=basic"]')
        next_link = None
        for item in next_page_tag:
            if '»' == item.css('a::text').extract_first():
                ori_link = item.css('a::attr(href)').extract_first()
                next_link = response.urljoin(ori_link)
        return next_link
