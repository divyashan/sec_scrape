import pandas as pd
import numpy as np
import sys
import os

from bs4 import BeautifulSoup
from utils import *

def scrape_files(path, save_file_name):
    fnames = os.listdir(path)
    fnames = [x for x in fnames if ('DS_Store' not in x)]
    results = []
    for fname in fnames:
        test_f = open(path + '/' + fname)
        wholetext = test_f.read()
        cik_re = get_cik(wholetext)
        datadate_re = get_datadate(wholetext)  

        wholetext = wholetext.lower()
        tbl_flag = 0 # 1 if "contractual obligations" table exists
        row_flag = 0 # 1 if "purchasing obligations" row exists
        multiplier = 1 # 1 by default

        # Scrape table and rows 
        rows = []
        table = scrape_table(wholetext)
        if table:
            tbl_flag = 1
            rows = scrape_rows(table)
            multiplier = get_multiplier_from_tbl(table)
        else:
            lines, tbl_list = scrape_text_table(wholetext)
            if tbl_list:
                tbl_flag = 1
                rows = scrape_text_rows(lines, tbl_list)
                multiplier = get_multiplier_from_tbl_list(tbl_list)

        # Iterate over scraped rows
        for row in rows:
            row_flag = 1
            result = {'fname': fname, 'cik': cik_re, 'datadate': datadate_re, 'tbl': tbl_flag, 'row': row_flag, 
                       '<1': row['<1'], '1-3':row['1-3'], '3-5':row['3-5'], '>5':row['>5'], 
                      'category': row['category'], 'multiplier': multiplier}
            if 'total' in row.keys():
                    result['total'] = row['total']
            results.append(result)

        # Add row for files with no rows
        if (tbl_flag == 0) or (row_flag == 0):
            result = {'fname': fname, 'cik': cik_re, 'datadate': datadate_re, 'tbl': tbl_flag, 'row': row_flag, 
                      'total': '-', '<1': '-', '1-3':'-', '3-5':'-', '>5':'-', 'multiplier': multiplier}

            results.append(result)
    pd.DataFrame(results).to_csv(save_file_name)
    
scrape_files(sys.argv[1], sys.argv[2])
