import scrapy
from scrapy.http import Request
from .. import items as myitems
import os
import json


class TaylorSpider(scrapy.Spider):
    name = 'taylor'
    allowed_domains = ['www.tandfonline.com', 'www-tandfonline-com.eproxy1.lib.hku.hk/']

    def form_query(self):
        # Allowing search in Keywords, Title, Authors or Anywhere
        # Each allows for AND and OR operator
        myquery = "/action/doSearch?field1=AllField&text1=pollution&field2=Keyword&text2="
        keys_Keywords = ['happiness', 'subjective well-being', 'life satisfaction', 'quality of life']
        return [myquery + '+'.join(i.split(' ')) for i in keys_Keywords]

    def start_requests(self):
        query_list = self.form_query()
        for query in query_list:
            start_url = "https://{dom}{q}".format(dom=self.allowed_domains[0], q=query)
            yield Request(url=start_url,
                          callback=self.parse_search_result_pages,
                          dont_filter=True)

    def parse_search_result_pages(self, response):
        file_url_whole = '{}_urls.json'.format(self.name)
        if file_url_whole not in os.listdir(os.getcwd()):
            url_whole = []
        else:
            with open(file_url_whole, 'r') as f:
                url_whole = json.load(f)

        articles = response.css('article.searchResultItem')
        a_urls = [a.css('div.art_title>span.hlFld-Title>a::attr(href)').extract_first() for a in articles]
        new_articles = [(i, j) for (i, j) in zip(a_urls, articles) if i not in url_whole]

        if new_articles:
            new_article_urls = [na[0] for na in new_articles]
            with open(file_url_whole, 'w') as f:
                json.dump(url_whole + new_article_urls, f)

            for url, a in new_articles:
                url = "https://{}{}".format(self.allowed_domains[0], url)
                paper = myitems.PaperItem()
                paper['type_article'] = a.css('div.article-type::text').extract_first() or ''
                paper['title'] = ' '.join(a.css('div.art_title>span.hlFld-Title>a ::text').extract()) or ''
                paper['link'] = url
                paper['author_list'] = [i.strip() for i in a.css('div.author span *::text').extract()]
                paper['journal_name'] = ' '.join(a.css('div.publication-meta a::text').extract()) or ''
                paper['date'] = a.css('span.publication-year::text').extract_first() or ''
                yield Request(url=url, callback=self.parse_article_page,
                              meta={'item': paper},
                              dont_filter=True)
        next_url = response.css('a.nextPage::attr(href)').extract_first()
        if next_url:
            yield Request(url='https://{}{}'.format(self.allowed_domains[0], next_url),
                          callback=self.parse_search_result_pages,
                          dont_filter=True)

    def parse_article_page(self, response):
        paper = response.meta.get('item')

        paper['abstract'] = '\n'.join(response.css('div.abstractSection p::text').extract()) or ''
        paper['doi'] = response.css('li.dx-doi a::attr(href)').extract_first() or ''
        paper['keyword_list'] = [i.strip() for i in response.css('div.hlFld-KeywordText *::text').extract()]
        paper['keyword_list'] = [i for i in paper['keyword_list'] if ('Key words' not in i) and (not i == ',')]
        paper['citation_count'] = 0  # need revision

        if 'full' in paper['link']:
            ref_url = paper['link'].replace('full', 'ref')
        elif 'abs' in paper['link']:
            ref_url = paper['link'].replace('abs', 'ref')
        yield Request(url=ref_url, callback=self.parse_ref_page, meta={'item': paper}, dont_filter=True)

    def parse_ref_page(self, response):
        paper = response.meta.get('item')
        paper['reference_list'] = [''.join(i.css('span *::text').extract()) for i in response.css('ul.references>li')]
        print('collected {} with {} references from {}'.format(paper['title'],
                                                               len(paper['reference_list']),
                                                               paper['link']))
        yield paper







