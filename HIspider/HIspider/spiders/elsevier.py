import scrapy
from scrapy.http import Request
from .. import items as myitems
from selenium import webdriver
import time
from scrapy.selector import Selector as sl


class ElsevierSpider(scrapy.Spider):
    name = 'elsevier'
    allowed_domains = ['www.sciencedirect.com', 'www-sciencedirect-com.eproxy2.lib.hku.hk']
    # start_url = "http://eproxy.lib.hku.hk/login?url=http://www.sciencedirect.com/"

    def __init__(self):
        self.driver = webdriver.Chrome()
        self.driver.get("http://eproxy.lib.hku.hk/login?url=http://www.sciencedirect.com/")
        inputs = self.driver.find_elements_by_css_selector('div.form-input>input')
        inputs[0].send_keys('zhiyilv')
        inputs[1].send_keys('lzhy09876poiuy')
        self.driver.find_element_by_css_selector('div.form-buttons>button').click()
        time.sleep(2)

    def form_query(self):
        myquery = "/search/advanced?"

        keys_all_words = ['pollution']
        keys_tak = ['happiness']

        if keys_all_words:
            myquery += "qs={}".format('%20'.join(keys_all_words))
        if keys_tak:
            myquery += "&tak={}".format('%20'.join(keys_tak))

        return myquery + "&show=100&sortBy=relevance"

    def start_requests(self):
        query = self.form_query()
        start_search_url = "https://www-sciencedirect-com.eproxy2.lib.hku.hk{}".format(query)
        yield Request(url=start_search_url,
                      cookies=self.driver.get_cookies(),
                      callback=self.parse_search_result_pages)
    # def parse(self, response):
    #     return scrapy.FormRequest.from_response(
    #         response,
    #         formcss='div.form-content',
    #         formdata={'text': 'zhiyilv', 'password': 'lzhy09876poiuy'},
    #         callback=self.after_login
    #     )

    # def after_login(self, response):
    #     if "Invalid HKU Portal UID/Library card number or PIN." in response.body:
    #         self.logger.error("Login failed")
    #         return
    #     # query = self.form_query()
    #     # start_search_url = "https://www-sciencedirect-com.eproxy2.lib.hku.hk{}".format(query)
    #     # yield Request(start_search_url, self.parse_search_result_pages)
    #     from scrapy.shell import inspect_response
    #     inspect_response(response, self)

    def parse_search_result_pages(self, response):
        article_urls = response.css('div.result-item-content>h2>a::attr(href)').extract()
        article_types = response.css('span.article-type::text').extract()
        for article_url, article_type in zip(article_urls, article_types):
            yield Request(url='https://www-sciencedirect-com.eproxy2.lib.hku.hk{}'.format(article_url),
                          cookies=self.driver.get_cookies(),
                          callback=self.parse_article_page,
                          meta={'type': article_type})
        next_url = response.css('li.pagination-link.next-link a::attr(href)').extract_first()
        if next_url:
            yield Request(url='https://www-sciencedirect-com.eproxy2.lib.hku.hk{}'.format(next_url),
                          cookies=self.driver.get_cookies(),
                          callback=self.parse_search_result_pages)

    def parse_article_page(self, response):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        paper = myitems.PaperItem()
        paper['link'] = response.url
        paper['type_article'] = response.meta.get('type') or ''

        ref_b = webdriver.Chrome()
        ref_b.get(response.url)
        for i in self.driver.get_cookies():
            ref_b.add_cookie(i)
        ref_b.get(response.url)
        time.sleep(0.8)

        response = sl(text=ref_b.page_source)

        paper['title'] = response.css('h1.Head span.title-text::text').extract_first() or ''
        paper['journal_name'] = response.css('h2.publication-title a.publication-title-link::text').extract_first() or ''
        paper['abstract'] = response.css('div.Abstracts p::text').extract_first() or ''
        paper['doi'] = response.css('a.doi::attr(href)').extract_first() or ''

        date = response.css("div.publication-volume>span.size-m::text").extract()
        date = [i.strip() for i in date if 'Pages' not in i]
        paper['date'] = ' '.join([i for i in date if not i == ',']) or ''

        citation_count = response.css('li.plx-citation span.pps-count::text').extract_first()
        if citation_count:
            paper['citation_count'] = int(citation_count.strip())
        else:
            paper['citation_count'] = 0

        paper['author_list'] = []
        for au in response.css("div.author-group a"):
            paper['author_list'].append(' '.join([au.css('span.text.given-name::text').extract_first(),
                                                  au.css('span.text.surname::text').extract_first()]))

        paper['keyword_list'] = response.css('div.Keywords>:first-child div.keyword span::text').extract()
        paper['reference_list'] = response.css('dd.reference strong.title::text').extract()

        ref_b.close()
        print('collected {} with {} references from {}'.format(paper['title'],
                                                               len(paper['reference_list']),
                                                               paper['link']))
        yield paper






