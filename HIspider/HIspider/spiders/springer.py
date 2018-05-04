import scrapy
from scrapy.http import Request
from .. import items as myitems
# from scrapy.loader import ItemLoader
import os
import json


class Springerspider(scrapy.Spider):
    name = 'springer'
    allowed_domains = ['link.springer.com']

    def form_query(self):
        myquery = '/search?date-facet-mode=between&showAll=true&facet-content-type=%22Article%22'

        # keys_all_words = ['pollution']
        # keys_exact_phrase = []
        # keys_least_words = ['air', 'environment', 'hazards', 'pollution']
        # keys_without_words = []
        # keys_title = []

        # if keys_title:
        #     myquery += '&dc.title={}'.format('+'.join(keys_title))
        # query = []
        # if keys_all_words:
        #     query.append('+AND+'.join(keys_all_words))
        # if keys_exact_phrase:
        #     query.append('%22{}%22'.format('+'.join(keys_exact_phrase)))
        # if keys_least_words:
        #     query.append('%28{}%29'.format('+OR+'.join(keys_least_words)))
        # if keys_without_words:
        #     query.append('NOT+%28{}%29'.format('+AND+'.join(keys_without_words)))
        # if query:
        #     myquery += '&query={}'.format('+AND+'.join(query))
        #
        # return myquery

        query_list = []
        # 1
        keys_all_words = ['pollution', 'happiness']
        query = []
        if keys_all_words:
            query.append('+AND+'.join(keys_all_words))
        if query:
            query_list.append(myquery + '&query={}'.format('+AND+'.join(query)))

        # 2
        keys_exact_phrase_list = ['subjective well-being', 'life satisfaction', 'quality of life']
        for kep in keys_exact_phrase_list:
            query_list.append(myquery + '&query=pollution+AND+%22{}%22'.format('+'.join(kep.split(' '))))

        return query_list

    def start_requests(self):
        query_list = self.form_query()
        for query in query_list:
            start_url = 'https://link.springer.com{}'.format(query)
            yield Request(start_url, self.parse_search_result_pages)
        # start_url = 'https://link.springer.com{}'.format(query)
        # print(start_url)
        # yield Request(start_url, self.parse_search_result_pages)

    def parse_search_result_pages(self, response):
        file_url_whole = 'springer_urls.json'
        if file_url_whole not in os.listdir(os.getcwd()):
            url_whole = []
        else:
            with open(file_url_whole, 'r') as f:
                url_whole = json.load(f)

        new_article_urls = [i for i in response.css('a.title::attr(href)').extract() if i not in url_whole]
        if new_article_urls:
            with open(file_url_whole, 'w') as f:
                json.dump(url_whole+new_article_urls, f)
            for article_url in new_article_urls:
                yield Request('https://link.springer.com{}'.format(article_url), self.parse_article_page)

        next_url = response.css('a.next::attr(href)').extract_first()
        if next_url:
            yield Request('https://link.springer.com{}'.format(next_url), self.parse_search_result_pages)

    def parse_article_page(self, response):
        # article_loader = myitems.PaperLoader(item=myitems.PaperItem(), response=response)
        # article_loader.add_css('title', 'h1.ArticleTitle::text')
        # article_loader.add_value('link', response.url)
        # article_loader.add_css('journal_name', 'span.JournalTitle::text')
        # article_loader.add_css('type_article', 'span.test-render-category::text')
        # article_loader.add_css('date', 'div.article-dates__entry time::text')
        # article_loader.add_css('abstract', 'section.Abstract>p::text')
        # article_loader.add_css('doi', 'span#doi-url::text')
        # article_loader.add_css('citation_count', 'ul#book-metrics span#citations-count-number::text')
        # article_loader.add_css('author_list', 'div.authors__list li span.authors__name::text')
        # article_loader.add_css('keyword_list', 'div.KeywordGroup span.Keyword::text')
        # ref_selector_list = response.css('li.Citation div.CitationContent')
        # for ref_s in ref_selector_list:
        #     ref_text_list = ref_s.css('::text').extract()
        #     ref_text = ' '.join([seg.strip() for seg in ref_text_list])
        #     article_loader.add_value('reference_list', ref_text)
        # return article_loader.load_item()
        paper = myitems.PaperItem()
        paper['title'] = response.css('h1.ArticleTitle::text').extract_first() or ''
        paper['link'] = response.url
        paper['journal_name'] = response.css('span.JournalTitle::text').extract_first() or ''
        paper['type_article'] = response.css('span.test-render-category::text').extract_first() or ''
        paper['date'] = response.css('div.article-dates__entry time::text').extract_first() or ''
        paper['abstract'] = response.css('section.Abstract>p::text').extract_first() or ''
        paper['doi'] = response.css('span#doi-url::text').extract_first() or ''
        citation_count = response.css('ul#book-metrics span#citations-count-number::text').extract_first()
        if citation_count:
            paper['citation_count'] = int(citation_count)
        else:
            paper['citation_count'] = 0
        paper['author_list'] = response.css('div.authors__list li span.authors__name::text').extract()
        paper['keyword_list'] = response.css('div.KeywordGroup span.Keyword::text').extract()
        paper['reference_list'] = []
        ref_selector_list = response.css('li.Citation div.CitationContent')
        for ref_s in ref_selector_list:
            ref_text_list = ref_s.css('::text').extract()
            ref_text = ' '.join([seg.strip() for seg in ref_text_list])
            paper['reference_list'].append(ref_text)
        print('collected {} with {} references from {}'.format(paper['title'],
                                                               len(paper['reference_list']),
                                                               paper['link']))
        yield paper

