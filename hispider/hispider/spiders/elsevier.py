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
            yield Request(url=start_url,
                          callback=self.parse_search_result_pages,
                          meta={'q': query, 'p': 1, 't': -1})  # p:current page number, t:total page number

    def parse_search_result_pages(self, response):
        file_url_whole = '{}_urls.json'.format(self.name)
        if file_url_whole not in os.listdir(os.getcwd()):
            url_whole = []
        else:
            with open(file_url_whole, 'r') as f:
                url_whole = json.load(f)

        articles = response.css('div.result-item-content')
        a_urls = [a.css('h2>a::attr(href)').extract_first() for a in articles]
        new_articles = [(i, j) for (i, j) in zip(a_urls, articles) if i not in url_whole]

        current_page = response.meta.get('p')
        query = response.meta.get('q')
        print('*******************  found {} new articles in page {} of query {}'.format(len(new_articles),
                                                                                         current_page,
                                                                                         query))

        if new_articles:
            new_article_urls = [na[0] for na in new_articles]
            with open(file_url_whole, 'w') as f:
                json.dump(url_whole + new_article_urls, f)

            for url, a in new_articles:
                paper = myitems.PaperItem()
                url = "https://{}{}".format(self.allowed_domains[0], url)
                paper['link'] = url
                paper['type_article'] = a.css('span.article-type::text').extract_first() or ''
                paper['title'] = ' '.join([seg.strip() for seg in a.css('h2>a *::text').extract()]) or ''
                paper['author_list'] = [i.strip() for i in a.css('ol>li>span.author::text').extract()]
                paper['journal_name'] = ''.join(a.css('div>ol>li *::text').extract()) or ''
                yield Request(url=url,
                              callback=self.parse_article_page,
                              meta={'item': paper},
                              dont_filter=True)

        total_page_count = response.meta.get('t')
        if total_page_count == -1:
            result_count_string = response.css('h1>span.search-body-results-text::text').extract_first().strip()
            result_count = int(result_count_string.replace(',', ''))
            total_page_count = int(result_count/100) + 1

        if current_page < total_page_count:  # there are more pages of search results
            next_url = 'https://{}{}&offset={}'.format(self.allowed_domains[0], query, 100*current_page)
            yield Request(url=next_url,
                          callback=self.parse_search_result_pages,
                          meta={'q': query, 'p': current_page+1, 't': total_page_count})
        # next_url = response.css('li.pagination-link.next-link a::attr(href)').extract_first()
        # page_count = 1
        # if next_url:
        #     page_count += 1
        #     print('^^^^^^^^^^ next page, page_count:{}'.format(page_count))
        #     yield Request(url='https://{}{}'.format(self.allowed_domains[0], next_url),
        #                   callback=self.parse_search_result_pages)

    def parse_article_page(self, response):
        # from scrapy.shell import inspect_response
        # inspect_response(response, self)
        paper = response.meta.get('item')
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

        paper['keyword_list'] = response.css('div.Keywords>:first-child div.keyword span::text').extract()
        paper['reference_list'] = response.css('dd.reference strong.title::text').extract()

        print('collected {} with {} words in abstract from {}'.format(paper['title'],
                                                                      len(paper['abstract']),
                                                                      paper['link']))
        yield paper






