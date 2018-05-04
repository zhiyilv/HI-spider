import scrapy
from scrapy.http import Request
from .. import items as myitems
import os
import json


class WileySpider(scrapy.Spider):
    name = 'wiley'
    allowed_domains = ['onlinelibrary.wiley.com']

    def form_query(self):
        # Allowing search in Keywords, Title, Authors or Anywhere
        # Each allows for AND and OR operator
        myquery = "/action/doSearch?field1=AllField&text1=pollution&field2=Keyword&text2="
        keys_Keywords = ['happiness', 'subjective well-being', 'life satisfaction', 'quality of life']
        return [myquery + '%20'.join(i.split(' ')) + '&Ppub=' for i in keys_Keywords]

    def start_requests(self):
        query_list = self.form_query()
        for query in query_list:
            start_url = "https://{dom}{q}".format(dom=self.allowed_domains[0], q=query)
            print('-----------------start searching {}'.format(query))
            yield Request(url=start_url,
                          callback=self.parse_search_result_pages,
                          dont_filter=True,
                          # p:current page number, tan:total article number, can:current article number
                          meta={'q': query, 'p': 1, 'tan': -1, 'can': 0})

    def parse_search_result_pages(self, response):
        file_url_whole = '{}_urls.json'.format(self.name)
        if file_url_whole not in os.listdir(os.getcwd()):
            url_whole = []
        else:
            with open(file_url_whole, 'r') as f:
                url_whole = json.load(f)

        articles = response.css('div.item__body')
        current_visited_article_number = response.meta.get('can')
        current_visited_article_number += len(articles)  # update the flag of last visited article number

        a_urls = [a.css('span.hlFld-Title>a::attr(href)').extract_first() for a in articles]
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
                url = "https://{}{}".format(self.allowed_domains[0], url)
                paper = myitems.PaperItem()
                paper['type_article'] = a.css('span.meta__type::text').extract_first() or ''
                paper['title'] = ''.join([seg.strip() for seg in a.css('span.hlFld-Title>a ::text').extract()]) or ''
                paper['link'] = url
                paper['author_list'] = [i.strip() for i in a.css('ul.meta__authors>li *::text').extract()]
                paper['journal_name'] = '|'.join([seg.strip() for seg in a.css('div.meta__details>a::text').extract()]) or ''
                paper['date'] = a.css('span.meta__epubDate::text').extract_first() or ''
                # paper['abstract']  # do not crawl abstract even though it is here
                yield Request(url=url, callback=self.parse_article_page,
                              meta={'item': paper},
                              dont_filter=True)

        result_count = response.meta.get('tan')
        if result_count == -1:
            result_count_string = response.css('span.result__count::text').extract_first().strip()
            result_count = int(result_count_string.replace(',', ''))
            print('++++++ ++++++++ there are totally {} articles for query {}'.format(result_count, query))

        if current_visited_article_number < result_count:  # there are more pages of search results
            next_url = 'https://{}{}&startPage={}'.format(self.allowed_domains[0], query, current_page)
            yield Request(url=next_url,
                          callback=self.parse_search_result_pages,
                          meta={'q': query, 'p': current_page + 1, 'tan': result_count, 'can':current_visited_article_number},
                          dont_filter=True)

    def parse_article_page(self, response):
        paper = response.meta.get('item')
        paper['doi'] = response.css('a.epub-doi::attr(href)').extract_first() or ''

        citation = response.css('div.epub-section.cited-by-count>span>a::text').extract_first()
        if citation:
            citation = int(citation.strip().replace(',', ''))
            paper['citation_count'] = citation
        else:
            paper['citation_count'] = 0

        ab_segs = response.css('div.article-section__content *::text').extract()
        if ab_segs:
            ab_segs = [seg.strip() for seg in ab_segs if seg.strip()]
        paper['abstract'] = '\n'.join(ab_segs) or ''

        paper['keyword_list'] = []  # need javascript
        # paper['keyword_list'] = [i.strip() for i in response.css('div.hlFld-KeywordText *::text').extract()]
        # paper['keyword_list'] = [i for i in paper['keyword_list'] if ('Key words' not in i) and (not i == ',')]
        paper['reference_list'] = []  # not provided

        print('collected {} with {} references from {}'.format(paper['title'],
                                                               len(paper['reference_list']),
                                                               paper['link']))
        yield paper






