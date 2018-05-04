import json
# import pickle
import openpyxl
import os


# class HispiderPipeline(object):
#     # def open_spider(self, spider):
#     #     try:
#     #         with open('title_list.pickle', 'rb') as f:
#     #             self.title_list = pickle.load(f)
#     #     except FileNotFoundError:
#     #         self.title_list = []
#     #
#     # def close_spider(self, spider):
#     #     with open('title_list.pickle', 'wb') as f:
#     #         pickle.dump(self.title_list, f)
#
#     def process_item(self, item, spider):
#         return item


class JsonWriterPipeline(object):
    def process_item(self, item, spider):
        line = json.dumps(dict(item)) + '\n'
        with open('{}_papers.jl'.format(spider.name), 'a') as f:
            f.write(line)
        return item


class ExcelWriterPipeline(object):

    def open_spider(self, spider):
        self.fn = '{}_papers.xlsx'.format(spider.name)
        if self.fn not in os.listdir(os.getcwd()):
            self.wb = openpyxl.Workbook()
            self.wb.active.append(['title', 'link', 'journal', 'type', 'date', 'abstract', 'doi',
                                   'citation_count', 'author', 'keywords', 'references'])
        else:
            self.wb = openpyxl.load_workbook(self.fn)

    def close_spider(self, spider):
        self.wb.save(self.fn)

    def process_item(self, item, spider):
        line = [item['title'], item['link'], item['journal_name'],
                item['type_article'], item['date'], item['abstract'],
                item['doi'], item['citation_count'],
                '\n'.join(item['author_list']),
                '\n'.join(item['keyword_list']),
                '\n'.join(item['reference_list'])]
        self.wb.active.append(line)

