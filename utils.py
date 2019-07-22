from operator import itemgetter 
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import re

from row_utils import *
from table_utils import *
from string_utils import *

debug = False

def get_cik_done(csv_name):
    # csv_name : name of CSV file of previous results
    # Returns a dictionary mapping CIKs to finished dates given a CSV file of results

    cik_done_dict = {}
    try: 
        done_df = pd.read_csv(save_file_name)
        pairs = done_df[['cik', 'datadate']].values
        cik_done_dict = {pair[0]: [] for pair in pairs }
        for cik, date in pairs:
            cik_done_dict[cik].append(date)
    except:
        pass
    return cik_done_dict

def scrape_table(wholetext):
    # wholetext : text string of SEC filing
    # Given a piece of text, identify table most likely to summarize contractual obligations

    # Identify all tables
    parsed_html = BeautifulSoup(wholetext)
    tables = parsed_html.find_all('table')
    if len(tables) == 0:
        if debug:
            print("No HTML tables!")
        return None
    
    # Search for 2003 regulation table
    keywords = ['contractual', 'obligations', 'lease', 'debt', 'payments due', 'total', 'capital', 'long-term']
    keywords = ['contractual', 'long-term', 'debt', 'obligations']
    contractual_tables = [table for table in tables if (kw in table.text for kw in keywords)]
    contractual_tables = [table for table in tables if len(table.text) < 2000] # remove tables of paragraphs
    if len(contractual_tables) == 0:
        if debug:
            print("No contractual tables!")
        return None
    
    # Identify most likely table
    table = most_likely_table(contractual_tables)
    if debug:
        print("Found a table") 
    return table

def scrape_rows(tbl):
    # tbl : HTML-type table
    # Given an HTML-type table, return relevant rows in dictionary format

    # Turn HTML-type table in list-of-lists table
    tbl_list = table_to_list(tbl)

    # Iterate over each row in list-of-lists
    rows = []
    for row in tbl_list:
        if len(row) == 0:
            continue
        # Clean row of garbage characters
        row = clean_row(row)
        # If clean_row(row) returns None, this is not a valid row
        # and we continue to the next row
        if not row: 
            continue
        # Checks if there are any row keywords in the first row element (the category)
        ignore_word_exists = any(row_kw in row[0] for row_kw in IGNORE_ROW_KWS)
        keyword_exists = any(row_kw in row[0] for row_kw in ROW_KWS)
        if keyword_exists and not ignore_word_exists:
            try:
                # Get header from table list to properly index columns
                hdrs = get_table_headers_from_list(tbl_list)

                # If hdrs is none, try identifying header from HTML-type table
                if not hdrs:
                    hdrs = get_table_headers(tbl)
                total_idx = get_total_idx(hdrs)
                
                # Check how long the row is -- this determines which 
                # row processing function we will use.
                if len(row) in process_row_fn.keys():
                    rows.append(process_row_fn[len(row)](row, total_idx))
                
                # If we don't have a row processing function for this 
                # row length, it's possible that the table includes extraneous
                # columns. Our last chance is the process_row_longer function.
                elif len(row) > 8 and len(hdrs) > 8: 
                    processed_row = process_row_longer(row, total_idx, hdrs)
                    if processed_row:
                        rows.append(processed_row)
                    else:
                        if debug:
                            print("Unable to parse longer row")
                            
            except Exception as e1:
                if debug:
                    print("Unknown error 1: ", e1, "-- processing as longer row")
                
                # If the preceding code ends in an error, 
                # try parsing row as a longer row. 
                if len(row) >=8 or len(hdrs) > 8:
                    try:
                        processed_row = process_row_longer(row, total_idx, hdrs)
                        if processed_row:
                            rows.append(processed_row)
                    except Except as e2:
                        if debug:
                            print("Error: ", e2)
    return rows


def scrape_text_table(wholetext):
    # wholetext : text string of SEC filing
    # Returns list-of-lists for lines and list-of-lists format table
    # The lines 
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
        multiplier = get_multiplier_from_string(final_text_chunk)
        lines = text_chunk_to_lines(final_text_chunk)
        tbl_list = clean_tbl_list(lines)
        tbl_list = combine_text_fields(tbl_list)
        #return final_text_chunk, multiplier, lines, tbl_list
        return multiplier, lines, tbl_list
    except Exception as e:
        return None, None, None

    
def scrape_text_rows(lines, tbl_list):
    rows = []
    for row in tbl_list:
        ignore_word_exists = any(row_kw in row[0] for row_kw in IGNORE_ROW_KWS)
        keyword_exists = any(row_kw in row[0] for row_kw in ROW_KWS)
        if keyword_exists and not ignore_word_exists:
            if ('following' not in row[0]) and ('less than' not in row[0]):
                cleaned_row = clean_row(row)
                if cleaned_row:
                    rows.append(cleaned_row)


    row_dicts = []
    hdr = get_table_headers_from_list(lines)
    if not hdr:
        return row_dicts
    
    try:
        total_idx = -1
        total_idxs = [idx for idx, s in enumerate(hdr) if 'total' in s]
        if len(total_idxs):
            total_idx = total_idxs[0]

        if len(rows[0]) == 6:
            for row in rows:
                row_dicts.append(process_row_len_6(row, total_idx))
        elif len(rows[0]) == 8:
            for row in rows:
                row_dicts.append(process_row_len_8(row, total_idx))
    except Exception as e:
        if debug:
            print("Unknown error: ", e)
        
        
    return(row_dicts)
