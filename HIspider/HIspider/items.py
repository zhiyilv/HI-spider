import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose


def link_together(item_list):
    return '\n'.join([i.strip() for i in item_list])


def clean_ref(item_ref):
    return item_ref


class PaperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    link = scrapy.Field()
    journal_name = scrapy.Field()
    type_article = scrapy.Field()
    date = scrapy.Field()
    abstract = scrapy.Field()
    doi = scrapy.Field()
    citation_count = scrapy.Field()
    author_list = scrapy.Field()
    keyword_list = scrapy.Field()
    reference_list = scrapy.Field()



