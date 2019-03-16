import scrapy
from scrapy.http import HtmlResponse

from New91Crawler.items import DownloadVideoItem, SaveMovieInfoItem


class MyFollowSpider(scrapy.Spider):
    name = 'MyFollow'
    cookie = ''

    def start_requests(self):
        me_main_url = 'http://91porn.com/my_subs.php'
        login_headers = {
            'Cookie': self.cookie,
            'Referer': 'http://91porn.com/index.php'
        }

        yield scrapy.Request(url=me_main_url, headers=login_headers)

    def parse(self, response: HtmlResponse):
        # 获取当前页面页数
        url_list = response.url.split('page=')
        if len(url_list) == 1:
            current_page_num = 1
        else:
            current_page_num = int(url_list[1])
        # 兼容 cookie 失效的情况
        if 'login.php' in response.url:
            raise ValueError('cookie 未设置或失效')
        else:
            myvideo_list = response.css('div.maindescwithoutborder')
            video_info_list = myvideo_list.css('a')
            self.logger.warn('解析{0}成功，存在{1}个视频'.format(response.url, len(video_info_list)))

            link_and_title_dict = {}
            for item in video_info_list:
                title = item.css('::text').extract_first()
                link = item.css('a::attr(href)').extract_first()
                # 不知道为啥有时候会出现 email protected
                if 'email protected' in title:
                    continue
                link_and_title_dict[link] = title
                # 丢给另一个去解析真实的视频地址
                yield scrapy.Request(url=link, callback=self.parse_my_follow_real_link)
            self.logger.warn('最终解析{0}个视频'.format(len(link_and_title_dict)))

            # 记录下来当前页面的内容
            yield SaveMovieInfoItem(page_number=current_page_num, movie_link_and_name=link_and_title_dict)

            self.logger.warn('解析完毕，检查是否存在下一页'.format(response.url))
            next_page_tag = response.css('a[href*="?&page="]')
            for i in next_page_tag:
                if '»' == i.css('a::text').extract_first():
                    ori_link = i.css('a::attr(href)').extract_first()
                    next_link = response.urljoin(ori_link)
                    self.logger.warn('存在下一页')
                    next_headers = {
                        'Cookie': self.cookie,
                        'Referer': response.url
                    }
                    yield scrapy.Request(url=next_link, callback=self.parse_me, headers=next_headers)

    def parse_my_follow_real_link(self, response: HtmlResponse):
        self.logger.warn('开始解析{0}真实视频'.format(response.url))
        title = response.css('#viewvideo-title::text').extract_first().strip()
        author = response.css('a[href*="uprofile.php"]').css('span::text').extract_first().strip()
        # 发现有的视频，名字相同，作者相同，只有Url中的viewkey不同
        view_key = response.url.split('viewkey=')[1]
        # 由于有的视频名字中带 / 会导致创建成文件夹，所以需要处理一下
        if '/' in title:
            title = title.replace('/', '')

        video_link = response.css('source::attr(src)').extract_first()
        if video_link:
            # 处理一下链接中 http://185.38.13.130//mp43/2998... 这种的 url
            video_link_list = video_link.split('//')
            real_video_link = video_link_list[0] + '//' + video_link_list[1] + '/' + video_link_list[2]
            self.logger.warn('视频:{0} 分析完毕,丢入下载 pipelines'.format(title))
            down_file_name = title + '-' + author + '-' + view_key
            yield DownloadVideoItem(file_urls=real_video_link, file_name=down_file_name)
        else:
            self.logger.warn('获取视频下载地址失败，地址：{0}'.format(response.url))
