# -*- coding: utf-8 -*-
from datetime import datetime
from w3lib.html import remove_tags

import scrapy
from scrapy import loader
from scrapy.loader.processors import TakeFirst, Compose, MapCompose


def date_processor(string_format):
    def sub_date_processor(date_string):
        """
        :param date_string: string date in format MM/DD/YYYY or DD/MM/YYYY
        :return: string date in format YYYY-MM-DD
        """
        return datetime.strptime(date_string, string_format).strftime("%Y-%m-%d")
    return sub_date_processor


class CompanyItem(scrapy.Item):
    name = scrapy.Field()
    phone = scrapy.Field()
    category = scrapy.Field()
    address = scrapy.Field()
    city = scrapy.Field()
    reviews = scrapy.Field()

    # i decided to keep this id cause i need it SQL tables, and it might be useful in any other cases
    _internal_id = scrapy.Field()


class ReviewItem(scrapy.Item):
    rating = scrapy.Field()
    review = scrapy.Field()
    date = scrapy.Field()


class BaseLoader(loader.ItemLoader):
    default_output_processor = TakeFirst()


class CompanyItemLoader(BaseLoader):
    default_item_class = CompanyItem
    reviews_out = MapCompose(dict)


class BaseReviewItemLoader(BaseLoader):
    default_item_class = ReviewItem
    default_output_processor = TakeFirst()

    review_out = Compose(TakeFirst(), remove_tags)


class UsReviewItemLoader(BaseReviewItemLoader):
    date_out = Compose(TakeFirst(), date_processor("%m/%d/%Y"))


class PtReviewItemLoader(BaseReviewItemLoader):
    date_out = Compose(TakeFirst(), date_processor("%d/%m/%Y"))
