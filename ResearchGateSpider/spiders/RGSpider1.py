# -*- coding: utf-8 -*-

from scrapy.spiders import CrawlSpider
from scrapy import Request, FormRequest
from scrapy.utils.request import request_fingerprint
from ResearchGateSpider.items import ResearchGateItem
from ResearchGateSpider.datafilter import DataFilter
from ResearchGateSpider.func import parse_text_by_multi_content
from scrapy.exceptions import CloseSpider
import pandas as pd
#from scrapy_splash import SplashRequest
#from scrapy_splash import SplashMiddleware
import time


class RGSpider1(CrawlSpider):
    name = 'RGSpider1'
    #name = "ResearchGateSpider"
    domain = 'https://www.researchgate.net'
    start_urls = pd.read_csv('/data/pure_chn_link.csv', header=None).ix[:, 0].tolist()
    # pub_item = []
    # finger_print = ''
    # start_urls = ['https://www.researchgate.net/profile/Anahid_A_Birjandi/contributions']

    def parse(self, response):
        return self.parse_candidate_overview(response)

    def parse_candidate_overview(self, response):
        if response.status == 429:
            lostitem_str = 'lost overview: ' + response.url
            self.lostitem_file.write(lostitem_str)
            self.lostitem_file.close()
            raise CloseSpider(reason='被封了，准备切换ip')
        print '-----------start to process: ' + response.url
        headers = response.request.headers
        headers["referer"] = response.url

        featured_researches = response.xpath('//div[contains(@class, "profile-highlights-publications")]').extract()
        address = DataFilter.simple_format(response.xpath('//div[contains(@class, "institution-location")]/text()').extract())
        add_list = address.split(',')
        add_len = len(add_list)
        if add_len == 3:
            city = add_list[0].strip()
            province = add_list[1].strip()
            country = add_list[2].strip()
        elif add_len == 2:
            city = add_list[0].strip()
            province = ''
            country = add_list[1].strip()
        elif add_len == 1:
            city = add_list[0].strip()
            province = ''
            country = ''
        else:
            city = address
            province = ''
            country = ''
        if featured_researches and country != 'China': 
            item = ResearchGateItem()

            item['person_key'] = request_fingerprint(response.request)
            item['fullname'] = DataFilter.simple_format(response.xpath('//a[@class = "ga-profile-header-name"]/text()').extract())
            item['target_sciences'] = DataFilter.simple_format(response.xpath('//*[@id="target-sciences"]/text()').extract())
            item['title'] = DataFilter.simple_format(response.xpath('//*[contains(@class,"profile-degree")]/div[@class="title"]/text()').extract())
            item['score'] = DataFilter.simple_format(response.xpath('//span[starts-with(@class, "score-link")]').extract())

            top_coauthors = response.xpath('//div[starts-with(@class, "authors-block")]//ul/li//h5[@class="ga-top-coauthor-name"]/a')
            item['co_authors'] = parse_text_by_multi_content(top_coauthors, "|")
            
            skills_expertise = response.xpath('//div[starts-with(@class, "profile-skills")]/ul/li//a[starts-with(@class, "keyword-list-token-text")]')
            item['skills'] = parse_text_by_multi_content(skills_expertise, "|")

            topics = response.xpath('//ul[@class="keyword-list clearfix"]/li//a[starts-with(@class, "keyword-list-token-text")]')
            item['topics'] = parse_text_by_multi_content(topics, "|")

            item['institution'] = DataFilter.simple_format(response.xpath('//div[starts-with(@class, "institution-name")]').extract())
            item['department'] = DataFilter.simple_format(response.xpath('//div[@class = "institution-dept"]').extract())
            
            item['city'] = city
            item['province'] = province
            item['country'] = country

            url = response.url + "/publications"
            print url
            return Request(url, headers=headers, callback=self.parse_contribution, dont_filter=True, meta={"item":item})
        else:
            print "--------Nothing to return, it is invalid--------"
        # yield Request(url, callback=self.parse_contribution, dont_filter=True, meta={"item":item})

    def parse_contribution(self, response):
        if response.status == 429:
            lostitem_str = 'lost contribution: ' + response.url
            self.lostitem_file.write(lostitem_str)
            self.lostitem_file.close()
            raise CloseSpider(reason=u'被封了，准备切换ip')
        headers = response.request.headers
        headers["referer"] = response.url
        # Parse articles, each article has a seperate page
        item = response.meta["item"]
        item['publications'] = []

        headers = response.request.headers
        headers["referer"] = response.url
        article_urls = response.xpath(
                '//li[contains(@class, "li-publication")]/descendant::a[contains(@class, "js-publication-title-link")]/@href').extract()
        article_count = len(article_urls)
        if article_count == 0:
            yield item
        for article_url in article_urls:
            article_url = self.domain + "/" + article_url
            yield Request(article_url, headers=headers, callback=self.parse_article, dont_filter=True, meta={'item':item, 'count':article_count})
        # for url in = article_urls[:3]:
        #     url = self.domain + "/" + url
        #     yield Request(url, headers=headers, callback=self.parse_article, dont_filter=True, meta={'item':item, 'last':'no'})
        
        
        # urls = response.xpath('//li[contains(@class, "li-publication")]/descendant::a[contains(@class, "js-publication-title-link")]/@href').extract()
        # url0 = self.domain + "/" + urls[0]
        # yield Request(url0, headers=headers, callback=self.parse_article, dont_filter=True)

    def parse_article(self, response):
        if response.status == 429:
            lostitem_str = 'lost article: ' + response.url
            self.lostitem_file.write(lostitem_str)
            self.lostitem_file.close()
            raise CloseSpider(reason='被封了，准备切换ip')
        print response.url
        # item = ResearchGateItem()
        item = response.meta['item']
        pub_count = response.meta['count']
        
        article_item = {}
        article_name = DataFilter.simple_format(response.xpath('//div[@class="publication-header"]//h1[@class="publication-title"]/text()').extract())
        article_item['article_name'] = article_name
        article_abstract = DataFilter.simple_format(response.xpath('//div[@class="publication-abstract"]/div[2]').extract())
        article_item['artical_abstract'] = article_abstract
        article_journal = DataFilter.simple_format(response.xpath('//span[@class="publication-meta-journal"]/a').extract())
        article_date = DataFilter.simple_format(response.xpath('//span[@class="publication-meta-date"]').extract())
        article_item['article_journal'] = article_journal + ", " + article_date
        item['publications'].append(article_item)
        if len(item['publications']) == pub_count:
            return item
    
    def __init__(self, **kwargs):
        self.lostitem_file = open('/data/pure_chinese_lost.out', 'a+')
        super(RGSpider1, self).__init__(**kwargs)
        pass

    def close(self, reason):
        self.lostitem_file.close()
        super(RGSpider1, self).close(self, reason)
