import json
from urllib.parse import urlparse

import scrapy
import jmespath

from reviewshake_test.items import CompanyItemLoader, UsReviewItemLoader, PtReviewItemLoader
from reviewshake_test.utils import change_query_parameter, extract_querystring


class YelpBaseSpider(scrapy.Spider):
    review_loader = None
    custom_settings = {
        'USER_AGENT': 'TelegramBot'
    }
    handle_httpstatus_list = [503]  # 503 is ban response

    def __init__(self, profile_url=None, list_url=None, *args, **kwargs):
        if not(profile_url or list_url):
            self.logger.error('Missing required profile_url or list_url')
            return

        super(YelpBaseSpider, self).__init__(*args, **kwargs)
        self._start_conf = (profile_url, self.parse) if profile_url else (list_url, self.parse_listing)

    def start_requests(self):
        url, callback = self._start_conf
        return [
            scrapy.Request(url, callback=callback)
        ]

    def parse_listing(self, response):
        for url in response.css('h4[class^="lemon--h4__373c0__1yd__"] a[href^="/biz/"]::attr(href)'):
            yield response.follow(url, callback=self.parse)
        next_page_url = response.css('link[rel="next"]::attr(href)').get()
        if next_page_url:
            yield response.follow(next_page_url, callback=self.parse_listing)

    def get_pagination_reviews_url(self, url, biz_id, start):
        return (
            "https://{0}/biz/{1}/review_feed?rl=en&sort_by=relevance_desc&q=&start={2}"
        ).format(urlparse(url).netloc, biz_id, start)

    def parse(self, response):
        if response.status == 503:
            self.logger.error('Ip is banned')
            return
        json_raw_data = response.css('div.main-content-wrap script[data-hypernova-key]::text').re_first("<!--(.*)-->")
        if not json_raw_data:
            self.logger.warning("No json data for page {0}".format(response.url))
            return
        try:
            json_data = json.loads(json_raw_data)
        except json.JSONDecodeError:
            self.logger.error("Error parsing json data for url: {0}".format(response.url))
            return

        biz_id = jmespath.search("bizDetailsPageProps.businessId", json_data)

        loader = CompanyItemLoader(response=response)
        loader.add_value('_internal_id', biz_id)
        loader.add_value("name", jmespath.search("bizDetailsPageProps.businessName", json_data))
        loader.add_value("phone", jmespath.search("bizDetailsPageProps.bizContactInfoProps.phoneNumber", json_data))
        loader.add_css('category', 'a[href^="/c/"]::text')
        loader.add_value(
            "address",
            jmespath.search("bizDetailsPageProps.mapBoxProps.addressProps.addressLines", json_data)
        )
        loader.add_value('city', jmespath.search("adSyndicationConfig.city", json_data))

        reviews_exists_on_html_page = response.xpath('//div[contains(@class, "i-stars--regular-")]').get()
        if not reviews_exists_on_html_page:
            yield loader.load_item()
            return

        review_data = jmespath.search('bizDetailsPageProps.reviewFeedQueryProps', json_data)
        reviews = list(self.proceed_reviews_data(review_data))
        for review in reviews:
            loader.add_value('reviews', review.load_item())

        if not reviews:
            # sometimes reviews are exists but not presented in json, so we need to make extra request for them
            pagination_url = self.get_pagination_reviews_url(url=response.url, biz_id=biz_id, start=0)
            yield response.follow(
                pagination_url,
                meta={'loader': loader},
                callback=self.proceed_reviews_pagination,
                headers={'x-requested-by-react': 'true', 'x-requested-with': 'XMLHttpRequest'}
            )
            return

        total_reviews = sum(jmespath.search(
            "bizDetailsPageProps.reviewFeedQueryProps.reviewLanguages[*].count", json_data
        ) or [])
        if total_reviews > 20:  # default reviews per page count
            pagination_url = self.get_pagination_reviews_url(url=response.url, biz_id=biz_id, start=20)
            yield response.follow(
                pagination_url,
                meta={'loader': loader},
                callback=self.proceed_reviews_pagination,
                headers={'x-requested-by-react': 'true', 'x-requested-with': 'XMLHttpRequest'}
            )
            return
        yield loader.load_item()

    def proceed_reviews_data(self, json_reviews_data):
        for review in json_reviews_data.get('reviews', []):
            review_loader = self.review_loader()
            review_loader.add_value('rating', review.get('rating'))
            review_loader.add_value('date', review.get('localizedDate'))
            review_loader.add_value('review', jmespath.search('comment.text', review))
            yield review_loader

    def proceed_reviews_pagination(self, response):
        loader = response.meta['loader']
        if response.status == 503:
            self.logger.error('Ip is banned')
            yield loader.load_item()
            return
        try:
            review_data = json.loads(response.text)
        except json.JSONDecodeError:
            self.logger.error('Error processing response {}'.format(response.url))
            return
        reviews = list(self.proceed_reviews_data(review_data))
        if not reviews:
            yield loader.load_item()
            return
        for review in reviews:
            loader.add_value('reviews', review.load_item())

        previous_start_index = extract_querystring(response.url).get('start')
        next_page_url = change_query_parameter(response.url, "start", int(previous_start_index) + 20)
        yield scrapy.Request(
            next_page_url,
            callback=self.proceed_reviews_pagination,
            meta=response.meta,
            headers={'x-requested-by-react': 'true', 'x-requested-with': 'XMLHttpRequest'}
        )


class YelpUsSpider(YelpBaseSpider):
    review_loader = UsReviewItemLoader
    name = "yelp.com_spider"


class YelpPtSpider(YelpBaseSpider):
    review_loader = PtReviewItemLoader
    name = "yelp.pt_spider"
