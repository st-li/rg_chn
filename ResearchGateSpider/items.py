# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field


class ResearchGateItem(Item):
    person_key = Field()
    fullname = Field()
    title = Field()
    target_sciences = Field()
    score = Field()
    co_authors = Field()
    topics = Field()
    skills = Field()
    institution = Field()
    department = Field()
    city = Field()
    province = Field()
    country = Field()
    publications = Field()
	