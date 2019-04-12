import scrapy
from scrapy.http.response.html import HtmlResponse

from New91Crawler.items import DownloadVideoItem
import New91Crawler.lib.ParseRealUrl as ParseRealUrl


class HottestVideoInThisMonthSpider(scrapy.Spider):
    name = 'Hottest'

    def start_requests(self):
        # 本月最热 的视频固定5页
        for i in range(1, 6):
            url = 'http://91porn.com/v.php?category=top&viewtype=basic&page={0}'.format(i)
            yield scrapy.Request(url)

    def parse(self, response: HtmlResponse):
        list_channel = response.css('div.listchannel')
        for item in list_channel:
            link = item.css('a::attr(href)').extract_first()
            title = item.css('a::attr(title)').extract_first()
            self.logger.warn('获取到视频:{0}'.format(title))
            yield scrapy.Request(url=link, callback=self.real_video_parse)

    def real_video_parse(self, response: HtmlResponse):
        title = response.css('#viewvideo-title::text').extract_first().strip()
        author = response.css('a[href*="uprofile.php"]').css('span::text').extract_first().strip()
        # 发现有的视频，名字相同，作者相同，只有Url中的viewkey不同
        view_key = response.url.split('viewkey=')[1].split('&')[0]
        # 由于有的视频名字中带 / 会导致创建成文件夹，所以需要处理一下
        if '/' in title:
            title = title.replace('/', '')

        encrypted_url = response.css('video').extract_first().split('strencode("')[1].split('"))')[0]
        first_encrypted = encrypted_url.split('"')[0]
        second_excrypted = encrypted_url.split('"')[2]
        video_link = ParseRealUrl.get_url(first_encrypted, second_excrypted)

        if video_link:
            # 处理一下链接中 http://185.38.13.130//mp43/2998... 这种的 url
            video_link_list = video_link.split('//')
            real_video_link = video_link_list[0] + '//' + video_link_list[1] + '/' + video_link_list[2]
            down_file_name = title + '-' + author + '-' + view_key
            yield DownloadVideoItem(file_urls=real_video_link, file_name=down_file_name)
        else:
            self.logger.warn('获取视频下载地址失败，地址：{0}'.format(response.url))
