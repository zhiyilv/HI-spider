import os
import json
import openpyxl



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





