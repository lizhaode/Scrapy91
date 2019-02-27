# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class DownloadVideoItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    file_urls = scrapy.Field()
    file_name = scrapy.Field()
    files = scrapy.Field()


class SaveMovieInfoItem(scrapy.Item):
    page_number = scrapy.Field()
    movie_link_and_name = scrapy.Field()


class UpdateMovieLinkItem(scrapy.Item):
    movie_page_url = scrapy.Field()
    movie_real_url = scrapy.Field()
