import pandas as pd
import numpy as np
import sys
import os
import re

from bs4 import BeautifulSoup
from utils import table_to_list, scrape_table, scrape_rows

path_2004 = "./2004/"
all_2004 = os.listdir(path_2004)

def scrape_files(path):
    fnames = os.listdir(path)
    results = []
    for fname in fnames:
        test_f = open(path + "/" + fname)
        wholetext = test_f.read()
        
        # Scrape CIK 
        cikbase = re.search(r"CENTRAL INDEX KEY:\s*?\d{10}\b", wholetext, re.I).group()
        cik_re = re.split(r'\s', cikbase)[-1]        

        # Scrape date
        datadatebase = re.search(r"CONFORMED PERIOD OF REPORT:\s*?\d{8}\b", wholetext, re.I).group() 
        datadate_re = re.split(r'\s', datadatebase)[-1]  

        # Identify table within text
        wholetext = wholetext.lower()
        tbl_flag = 0 # 1 if "contractual obligations" table exists
        row_flag = 0 # 1 if "purchasing obligations" row exists
        table = scrape_table(wholetext)
        
        # If table exists, scrape row from table
        rows = []
        if table:
            tbl_flag = 1
            rows = scrape_rows(table)
        else:
            # Look for non-HTML tables
            tbl_list = scrape_text_table(wholetext)
            if tbl_list:
                tbl_flag = 1
                rows = scrape_text_rows(tbl_list)
        
        # If row exists, append information to dataframe
        for row in rows:
            row_flag = 1
            result = {'fname': fname, 'cik': cik_re, 'datadate': datadate_re, 'tbl': tbl_flag, 'row': row_flag, 
                      'total': row['total'], '<1': row['<1'], '1-3':row['1-3'], '3-5':row['3-5'], '>5':row['>5'], 
                      'category': row['category']}
            results.append(result)
            
            
        # Append null row for file with no found table or no found row
        if (tbl_flag == 0) or (row_flag == 0):
            result = {'fname': fname, 'cik': cik_re, 'datadate': datadate_re, 'tbl': tbl_flag, 'row': row_flag, 
                      'total': '-', '<1': '-', '1-3':'-', '3-5':'-', '>5':'-'}

            results.append(result)
    pd.DataFrame(results).to_csv('scraped_data_df')
    
scrape_files(sys.argv[1])