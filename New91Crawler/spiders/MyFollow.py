import scrapy
from scrapy.http import HtmlResponse

from New91Crawler.items import DownloadVideoItem, SaveMovieInfoItem


class MyFollowSpider(scrapy.Spider):
    name = 'MyFollow'
    cookie = '__cfduid=d63e81e1955407b501c5042111fd962671548926438; __utmz=50351329.1548926440.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); __dtsu=D9E9B66BE8BD525C1373DB3602A5D655; 91username=082aVgUwRYBsuTTSsGncSC7V5KB0R%2FOqkMx%2BS1Ce%2FXbWZkMfzJQzruw; __utma=50351329.666365717.1548926440.1550404739.1550535152.33; __utmb=50351329.0.10.1550535152; __utmc=50351329; CLIPSHARE=n7k00qlco3g05bk52f9u5h0k37; __51cke__=; DUID=6a6duFUD5MUSpDSjT%2FDbvpzw8G3iL%2FYU%2BkrWuD7cIB6ykaHM; USERNAME=b9c06G3Vr%2B3%2FnegqL0uoaY9EqCqP%2FO5891Jo9i6MCyygp4f58PodIlY; user_level=1; EMAILVERIFIED=yes; level=1; __tins__3878067=%7B%22sid%22%3A%201550535153533%2C%20%22vd%22%3A%205%2C%20%22expires%22%3A%201550536979045%7D; __51laig__=5'

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
            url_list = response.url.split('page=')
            if len(url_list) == 1:
                current_page_num = 1
            else:
                current_page_num = int(url_list[1])
            yield SaveMovieInfoItem(page_number=current_page_num, movie_link_and_name=link_and_title_dict)

            if current_page_num <= 20:
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
        # 由于有的视频名字中带 / 会导致创建成文件夹，所以需要处理一下
        if '/' in title:
            title = title.replace('/', '')

        video_link = response.css('source::attr(src)').extract_first()
        if video_link:
            # 处理一下链接中 http://185.38.13.130//mp43/2998... 这种的 url
            video_link_list = video_link.split('//')
            real_video_link = video_link_list[0] + '//' + video_link_list[1] + '/' + video_link_list[2]
            self.logger.warn('视频:{0} 分析完毕,丢入下载 pipelines'.format(title))
            yield DownloadVideoItem(file_urls=real_video_link, file_name=title + '-' + author)
        else:
            self.logger.warn('获取视频下载地址失败，地址：{0}'.format(response.url))
