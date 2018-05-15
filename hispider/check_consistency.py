import os
import json
import openpyxl
import pandas as pd
from selenium import webdriver
import time
from scrapy.selector import Selector


def check():
    publishers = ['springer', 'elsevier', 'taylor', 'wiley']

    # print(os.listdir(os.getcwd()))

    for p in publishers:
        if '{}_urls.json'.format(p) in os.listdir(os.getcwd()):
            with open('{}_urls.json'.format(p), 'r') as f:
                uj = json.load(f)
            url_count = len(uj)

            wb = openpyxl.load_workbook('{}_papers.xlsx'.format(p))
            info_count = wb.active.calculate_dimension().split(':')[1][1:]
            info_count = int(info_count) -1  # minus the header

            if info_count == url_count:
                print('{} is consistent, '.format(p), end='')
            else:
                print('{} is inconsistent, '.format(p), end='')
            print('{} info and {} urls'.format(info_count, url_count))


def form_query():
    allowed_domains = ['link.springer.com', 'www.sciencedirect.com', 'www.tandfonline.com', 'onlinelibrary.wiley.com']
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
    return query_list


def complete():  # only for wiley
    name = 'complete_taylor'
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['title', 'link', 'journal', 'type', 'date', 'abstract', 'doi',
               'citation_count', 'author', 'keywords', 'references'])

    q_list = form_query()[2]
    b = webdriver.Chrome()
    for url in q_list:
        b.get(url)
        time.sleep(2)
        paper = dict()
        paper['link'] = url

        response = Selector(text=b.page_source)
        paper['type_article'] = response.css('div.toc-heading>h3::text').extract_first().strip()
        paper['title'] = response.css('div.wrapped>div>h1>span::text').extract_first().strip()
        paper['author_list'] = [i.strip() for i in response.css('span.NLM_contrib-group>span>a::text').extract()]
        paper['journal_name'] = response.css('div.title-container>h1>a::text').extract_first().strip()
        paper['date'] = response.css('div.itemPageRangeHistory').extract_first().split(':')[-1]
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

        response = Selector(text=b.page_source)
        paper['reference_list'] = [''.join(i.css('span *::text').extract()) for i in response.css('ul.references>li')]
        print('collected {} with {} references from {}'.format(paper['title'],
                                                               len(paper['reference_list']),
                                                               paper['link']))
        # write json lines
        line = json.dumps(paper) + '\n'
        with open('{}_papers.jl'.format(name), 'a') as f:
            f.write(line)

        # write excel lines
        item = paper
        line = [item['title'], item['link'], item['journal_name'],
                item['type_article'], item['date'], item['abstract'],
                item['doi'], item['citation_count'],
                '\n'.join(item['author_list']),
                '\n'.join(item['keyword_list']),
                '\n'.join(item['reference_list'])]
        ws.append(line)

    wb.save('{}_papers.xlsx'.format(name))


if __name__ == '__main__':
    complete()






