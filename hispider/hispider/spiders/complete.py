import scrapy
from scrapy.http import Request
from .. import items as myitems
import os
import json
import pandas as pd
from selenium import webdriver
import time


class Completespider(scrapy.Spider):
    name = 'complete'

    def form_query(self):
        allowed_domains = ['link.springer.com', 'www.sciencedirect.com', 'www.tandfonline.com',
                           'onlinelibrary.wiley.com']
        publishers = ['springer', 'elsevier', 'taylor', 'wiley']
        query_list = [[], [], [], []]
        file_folder = 'E:\Projects\HI-spider\hispider'
        for publisher_index in range(4):
            pub = publishers[publisher_index]
            file_url_json = os.path.join(file_folder, '{}_urls.json'.format(pub))
            file_excel = os.path.join(file_folder, '{}_papers.xlsx'.format(pub))
            with open(file_url_json, 'r') as f:
                url_list = json.load(f)
            df = pd.read_excel(file_excel)
            collected_url = set(list(df['link']))
            for url in url_list:
                url_full = 'https://{}{}'.format(allowed_domains[publisher_index], url)
                if url_full not in collected_url:
                    query_list[publisher_index].append(url_full)
            print('found {} missing urls for {}'.format(len(query_list[publisher_index]), pub))
        return query_list[2]  # only taylor needs to be completed

    def start_requests(self):
        query_list = self.form_query()
        for url in query_list:
            paper = myitems.PaperItem()
            paper['link'] = url
            b = webdriver.Chrome()
            yield self.parse_article_page(paper, b)

    def parse_article_page(self, paper, b):
        b.get(paper['link'])
        time.sleep(2)
        response = scrapy.selector.Selector(text=b.page_source)
        paper['type_article'] = response.css('div.toc-heading>h3::text').extract_first().strip()
        paper['title'] = response.css('div.toc-heading h1>span::text').extract_first().strip()
        paper['author_list'] = [i.strip() for i in response.css('span.NLM_contrib-group>span>a::text').extract()]
        paper['journal_name'] = response.css('div.title-container>h1>a::text').strip()
        paper['date'] = response.css('div.itemPageRangeHistory').split(':')[-1]
        paper['abstract'] = '\n'.join(response.css('div.abstractSection p::text').extract()) or ''
        paper['doi'] = response.css('li.dx-doi a::attr(href)').extract_first() or ''
        paper['keyword_list'] = [i.strip() for i in response.css('div.hlFld-KeywordText *::text').extract()]
        paper['keyword_list'] = [i for i in paper['keyword_list'] if ('Key words' not in i) and (not i == ',')]
        paper['citation_count'] = 0  # need revision

        if 'full' in paper['link']:
            ref_url = paper['link'].replace('full', 'ref')
        elif 'abs' in paper['link']:
            ref_url = paper['link'].replace('abs', 'ref')
        b.get(ref_url)
        time.sleep(2)
        yield self.parse_ref_page(paper, b)

    def parse_ref_page(self, paper, b):
        response = scrapy.selector.Selector(text=b.page_source)
        paper['reference_list'] = [''.join(i.css('span *::text').extract()) for i in response.css('ul.references>li')]
        print('collected {} with {} references from {}'.format(paper['title'],
                                                               len(paper['reference_list']),
                                                               paper['link']))
        b.close()
        yield paper

