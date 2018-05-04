import scrapy
from scrapy.http import Request
from .. import items as myitems
# from selenium import webdriver
# import time
# from scrapy.selector import Selector as sl
import json
import os


class ElsevierSpider(scrapy.Spider):
    name = 'elsevier'
    allowed_domains = ['www.sciencedirect.com', 'www-sciencedirect-com.eproxy2.lib.hku.hk']

    def form_query(self):
        myquery = "/search/advanced?qs=pollution"

        # keys_all_words = ['pollution']
        # myquery += "qs={}".format('%20'.join(keys_all_words))

        query_list = []
        # 1
        keys_tak = ['happiness']
        query_list.append(myquery + "&tak={}&show=100&sortBy=relevance".format('%20'.join(keys_tak)))

        # 2
        keys_tak_list = ['subjective well-being', 'life satisfaction', 'quality of life']
        for kep in keys_tak_list:
            query_list.append(myquery + '&tak={}&show=100&sortBy=relevance'.format('%20'.join(kep.split(' '))))

        return query_list

    def start_requests(self):
        query_list = self.form_query()
        for query in query_list:
            start_url = 'https://{}{}'.format(self.allowed_domains[0], query)
            print('-----------------start search {}'.format(query))
            yield Request(start_url, self.parse_search_result_pages)

    def parse_search_result_pages(self, response):
        file_url_whole = '{}_urls.json'.format(self.name)
        if file_url_whole not in os.listdir(os.getcwd()):
            url_whole = []
        else:
            with open(file_url_whole, 'r') as f:
                url_whole = json.load(f)

        article_urls = response.css('div.result-item-content>h2>a::attr(href)').extract()
        article_types = response.css('span.article-type::text').extract()

        new_articles = [(i, j) for (i, j) in zip(article_urls, article_types) if i not in url_whole]
        print('*******************  found {} new articles'.format(len(new_articles)))

        if new_articles:
            new_article_urls = [i[0] for i in new_articles]
            with open(file_url_whole, 'w') as f:
                json.dump(url_whole + new_article_urls, f)

            for u, t in new_articles:
                yield Request(url='https://{}{}'.format(self.allowed_domains[0], u),
                              callback=self.parse_article_page,
                              meta={'type': t})

        next_url = response.css('li.pagination-link.next-link a::attr(href)').extract_first()
        page_count = 1
        if next_url:
            page_count += 1
            print('^^^^^^^^^^ next page, page_count:{}'.format(page_count))
            yield Request(url='https://{}{}'.format(self.allowed_domains[0], next_url),
                          callback=self.parse_search_result_pages)

    def parse_article_page(self, response):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        paper = myitems.PaperItem()
        paper['link'] = response.url
        paper['type_article'] = response.meta.get('type') or ''
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

        print('collected {} with {} words in abstract from {}'.format(paper['title'],
                                                                      len(paper['abstract']),
                                                                      paper['link']))
        yield paper






