import pandas as pd
from bs4 import BeautifulSoup
from operator import itemgetter 

import numpy as np
import re
import itertools
import six

from row_utils import *

def get_cik(wholetext):
    cikbase = re.search(r"CENTRAL INDEX KEY:\s*?\d{10}\b", wholetext, re.I).group()
    cik_re = re.split(r'\s', cikbase)[-1]        
    return cik_re

def get_datadate(wholetext):
    datadatebase = re.search(r"CONFORMED PERIOD OF REPORT:\s*?\d{8}\b", wholetext, re.I).group() 
    datadate_re = re.split(r'\s', datadatebase)[-1]  
    return datadate_re

def get_multiplier_from_tbl_list(table_list):
    table_string = ' '.join([' '.join(row) for row in table_list])
    if 'thousands' in table_string:
        return 1000
    elif 'millions' in table_string:
        return 1000000
    elif 'billions' in table_string:
        return 1000000
    return 1

def get_multiplier_from_tbl(table):
    # Look at table string
    table_list = table_to_list(table)
    multiplier = get_multiplier_from_tbl_list(table_list)
    if multiplier > 1:
        return multiplier
    
    # Look at preceding text
    n_prev_siblings = 6
    preceding_text = ' '.join([str(x) for x in itertools.islice(table.previous_siblings, n_prev_siblings)])
    thousands_idx = preceding_text.index('thousands') if 'thousands' in preceding_text else float('inf')
    millions_idx = preceding_text.index('millions') if 'millions' in preceding_text else float('inf')
    billions_idx = preceding_text.index('billions') if 'billions' in preceding_text else float('inf')
    
    multipliers = [1000, 1000000, 1000000000]
    multiplier_idxs = [thousands_idx, millions_idx, billions_idx]
    if np.any([x < float('inf') for x in multiplier_idxs]):
        # Choose earliest occuring denomination
        return multipliers[np.argmin(multiplier_idxs)]
    
    # Default return 1
    return 1


def transpose_list(tbl_list):
    if len(tbl_list) > 2: 
        if len(tbl_list[0]) != len(tbl_list[2]):
            # Header has one less entry than the following rows
            # Important to preserve this as we transpose tables
            first_row = ['HEADER']
            first_row.extend(tbl_list[0])
            tbl_list[0] = first_row
        if len(tbl_list[1]) != len(tbl_list[2]):
            # Header has one less entry than the following rows
            # Important to preserve this as we transpose tables
            second_row = ['HEADER']
            second_row.extend(tbl_list[1])
            tbl_list[1] = second_row
    return list(map(list, six.moves.zip_longest(*tbl_list, fillvalue='-')))

def table_to_list(table):
    # Given a table in HTML format, return a list of lists 
    data = []
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        row = [ele for ele in cols if ele]
        row = [ele for ele in cols if ele]
        if len(row) > 0:
            data.append(row) 
    
    if is_transposed(data):
        transposed = transpose_list(data)
        return (combine_text_fields(transposed))
    
    return combine_text_fields(data)

def get_table_headers(table):
    tbl_list = table_to_list(table)
    hdr_row = get_table_headers_from_list(tbl_list)
    if hdr_row:
        return hdr_row
    
    column_name_elim_words = [ 'amounts due by fiscal year']
    elim_subwords = ['\xa0','thousands', 'millions']
    table_headers = [x.text for x in table.find_all('th')]
    if len(table_headers) == 0:
        table_headers = [x.text for x in table.find('tr').find_all('td')]
    table_headers = [x for x in table_headers if (x not in column_name_elim_words)]
    table_headers = [a.replace('\n', '') for a in table_headers]
    final_table_headers = []
    for header in table_headers:
        if not any(elim_word in header for elim_word in elim_subwords):
            final_table_headers.append(header)
            
    return final_table_headers

def get_table_headers_from_list(tbl_list):
    for row in tbl_list:
        row_str = ' '.join(row)
        if any(hdr_kw in row_str for hdr_kw in HDR_KWS):
            return row
    
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def hasKeywords(inputString, keywords):
    return any([word in inputString for word in keywords])

def is_transposed(tbl_list):
    # True if any header keywords appear in first row
    first_col = [x[0] for x in tbl_list if (len(x) > 0)]
    n_hdr_kws = sum([any([hdr_kw in x for x in first_col]) for hdr_kw in HDR_KWS_WITHOUT_TOTAL])
    return (n_hdr_kws > 1)

def combine_text_fields(lines):
    tbl_list = []
    for i, line in enumerate(lines):
        new_line = []
        for j, word in enumerate(line):
            if (hasNumbers(word)) or ('-' in word):
                new_line.append(word)
            else:
                if len(new_line) > 0 and j > 0:
                    if not(hasNumbers(new_line[len(new_line)-1])):
                        new_line[len(new_line)-1] = new_line[len(new_line)-1] + " " + word
                    else:
                        new_line.append(word)
                else:
                    new_line.append(word)
        tbl_list.append(new_line)
    return tbl_list

def most_likely_table(tables):
    # Given a list of tables, identify the most likely table to summarize contractual obligations
    if len(tables) == 1:
        return tables[0]
    
    table_scores = np.zeros(len(tables))
    keywords = ['obligations', 'leases', 'debt', 'total', 'operating', 'capital', 'long-term', 'payments due', 'borrowings', 'long term', 'due by period', '2006-2007']
    # took out total because its a non-specific word -- if performance dips, add it back in
    
    for i, table in enumerate(tables):
        for word in keywords:
            if table.text.count(word) > 0:
                table_scores[i] += 1
    max_score = np.max(table_scores)
    max_idxs = np.where(table_scores == max_score)[0]
    # for debugging
    #return table_scores, tables

    if len(max_idxs) == 1:
        return tables[max_idxs[0]]
    
    else:
        min_length = float('inf')
        for idx in max_idxs:
            if len(tables[idx].text) < min_length:
                min_length_table = tables[idx]
                min_length = len(min_length_table.text)
        return min_length_table

def scrape_table(wholetext):
    # Given a piece of text, identify table most likely to summarize contractual obligations

    # Identify all tables
    parsed_html = BeautifulSoup(wholetext)
    tables = parsed_html.find_all('table')
    if len(tables) == 0:
        print("No HTML tables!")
        return None
    
    # Search for 2003 regulation table
    keywords = ['contractual', 'obligations', 'lease', 'debt', 'payments due', 'total', 'capital', 'long-term']
    keywords = ['contractual', 'long-term', 'debt', 'obligations']
    contractual_tables = [table for table in tables if (kw in table.text for kw in keywords)]
    contractual_tables = [table for table in tables if len(table.text) < 2000] # remove tables of paragraphs
    if len(contractual_tables) == 0:
        print("No contractual tables!")
        return None
    
    # Identify most likely table
    table = most_likely_table(contractual_tables)
    print("Found a table") 
    return table

def scrape_rows(tbl):
    tbl_list = table_to_list(tbl)
    rows = []
    for row in tbl_list:
        if len(row) == 0:
            continue
        row = clean_row(row)
        if any(row_kw in row[0] for row_kw in ROW_KWS):
            # TODO: ensure that all the columns add up to 'total'
            # TODO: multiple by 1000 in case value reported < 100  
            try:
              
                hdrs = get_table_headers_from_list(tbl_list)
                if not hdrs:
                    hdrs = get_table_headers(tbl)
                total_idx = -1
                total_idxs = [idx for idx, s in enumerate(hdrs) if 'total' in s]
                if len(total_idxs):
                    total_idx = total_idxs[0]
                #print("HEADER: ", hdrs)
                #print("total idx: ", total_idx)
                #print("Row: ", row)
                #print("Row length: ", len(row), len(hdrs))
                if len(row) in process_row_fn.keys():
                    rows.append(process_row_fn[len(row)](row, total_idx))
                elif len(row) > 8 and len(hdrs) > 8: 
                    processed_row = process_row_longer(row, total_idx, hdrs)
                    if processed_row:
                        rows.append(processed_row)
                    else:
                        print("Unable to parse longer row")
            except Exception as e1:
                print("Unknown error 1: ", e1, "-- processing as longer row")
                if len(row) >=8 or len(hdrs) > 8:
                    try:
                        processed_row = process_row_longer(row, total_idx, hdrs)
                        if processed_row:
                            rows.append(processed_row)
                    except Except as e2:
                        print("Error: ", e2)
    return rows


def scrape_text_table(wholetext):
    try: 
        idxs =  [a.start() for a in list(re.finditer('contractual', wholetext))]
        text_chunks = [wholetext[idx:idx+4000] for idx in idxs]
        chunk_scores = np.zeros(len(text_chunks))
        keywords = ['contractual obligations', 'long-term debt', 'operating leases']
        for i,text_chunk in enumerate(text_chunks):
            for word in keywords:
                if word in text_chunk:
                    chunk_scores[i] += 1
        #return text_chunks, chunk_scores

        final_text_chunk = text_chunks[np.argmax(chunk_scores)]
        lines = final_text_chunk.split('\n')
        lines = [x for x in lines if (hasNumbers(x))]
        keywords = HDR_KWS + ROW_KWS
        lines = [x for x in lines if (hasKeywords(x, keywords))]
        lines = [x.split(' ') for x in lines]
        for i, line in enumerate(lines):
            lines[i] = list(filter(lambda a: (a != '') and (a != '$') and (a !='<u>') and (a !='</u>'), line))    
        tbl_list = []
        tbl_list = combine_text_fields(lines)
        return lines, tbl_list
    except Exception as e:
        return None, None

    
def scrape_text_rows(lines, tbl_list):
    rows = []
    for row in tbl_list:
        if any([word in row[0] for word in ROW_KWS]):
            if ('following' not in row[0]) and ('less than' not in row[0]):
                cleaned_row = clean_row(row)
                if cleaned_row:
                    rows.append(cleaned_row)

    print("ROWS")
    print(rows)
    row_dicts = []
    hdr = get_table_headers_from_list(lines)
    if not hdr:
        print("Returning: ", row_dicts)
        return row_dicts
    
    try:
        total_idx = -1
        total_idxs = [idx for idx, s in enumerate(hdr) if 'total' in s]
        if len(total_idxs):
            total_idx = total_idxs[0]
        print("total_idx: ", total_idx)
        print(rows[1])
        if len(rows[0]) == 6:
            for row in rows:
                row_dicts.append(process_row_len_6(row, total_idx))
        elif len(rows[0]) == 8:
            for row in rows:
                row_dicts.append(process_row_len_8(row, total_idx))
    except Exception as e:
        print("Unknown error: ", e)
        
        
    return(row_dicts)