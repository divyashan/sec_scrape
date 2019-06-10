import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import re

# def table_denomination(table):
    # searches through table text for thous or mill or bill
    # if none of these are found, looks at the parent element for mentions of these
    # otherwise, assumes that these rows are reporting raw values (maybe include a check that they're in a certain range)

# def detect_transpose(table):
    # check if table is transposed or not
    # 

row_kws = ["advertis","aircraft","build","buy","capacit","capex","capital","commercial","consult",
          "clinical","collaborat","construct","consumer","customer","deliver","develop","distribut",
          "drug","engineer","equipment","estate","exclusiv","expand","expansion","facility","facilities",
          "factory","factories","fuel","hardware","infrastructur","innovat","invent","invest","joints+venture",
          "land","license","licensing","manufactur","marketing","material","merchandis","operat","outsourc",
          "patent","plant","procure","product","project","property","properties","purchas","research","research",
          "R & D","right","royalt","science","scientist","sell","software","store","sponsor","storage","supplie",
          "supply","technology","truck","vehicle", "transportation"]
def table_to_list(table):
    # Given a table in HTML format, return a list of lists 
    # TODO: make sure table is returned in row format
    data = []
    rows = table.find_all('tr')
    for row in rows:
        cols = row.find_all('td')
        cols = [ele.text.strip() for ele in cols]
        row = [ele for ele in cols if ele]
        data.append([ele for ele in cols if ele]) 
    return data

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
    hdr_kws = ['2005', '2006', '2007', '2008', '2009', 'thereafter', 'total']
    for row in tbl_list:
        row_str = ' '.join(row)
        if any(hdr_kw in row_str for hdr_kw in hdr_kws):
            return row
    
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def hasKeywords(inputString, keywords):
    return any([word in inputString for word in keywords])

def clean_row(row):
    row = [x for x in row if (x != '$')] # remove lone $ entries
    row = [a.replace('$', '') for a in row] 
    row = [a.replace(',', '') for a in row] 
    row = [x for x in row if (x != '')]
    row = [a.replace('\x97', '0') for a in row]
    row = [a.replace('\xa0', '') for a in row]
    row = [a.replace('-', '0') for a in row]

    return row

def most_likely_table(tables):
    # Given a list of tables, identify the most likely table to summarize contractual obligations
    if len(tables) == 1:
        return tables[0]
    
    table_scores = np.zeros(len(tables))
    keywords = ['obligations', 'lease', 'debt', 'operating', 'total', 'capital', 'long-term', 'payments', 'borrowings', 'long term']
    
    for i, table in enumerate(tables):
        for word in keywords:
            if table.text.count(word) > 0:
                table_scores[i] += 1
    max_score = np.max(table_scores)
    max_idxs = np.where(table_scores == max_score)[0]
    #return table_scores, tables

    if len(max_idxs) == 1:
        return tables[max_idxs[0]]
    
    else:
        min_length_table = tables[max_idxs[0]]
        min_length = len(min_length_table.text)
        for idx in max_idxs:
            if len(tables[idx].text) < min_length:
                min_length_table = tables[idx]
                min_length = len(min_length_table)
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
        if any(row_kw in row[0] for row_kw in row_kws):
            # TODO: ensure that all the columns add up to 'total'
            # TODO: multiple by 1000 in case value reported < 100            
            try:
                if len(row) == 5:
                    headers = get_table_headers(tbl)
                    total_idx = [idx for idx, s in enumerate(headers) if 'total' in s][0]
                    four_condition = any([('4' in x) or ('four' in x) for x in headers])
                    if total_idx < 3:
                        rows.append({'total': float(row[1]), '<1':row[2], '1-3':row[3], '3-5':'-', '>5':row[4], 'category':row[0]})
                    else:
                        rows.append({'total': float(row[4]), '<1':row[1], '1-3':row[2], '3-5':'-', '>5':row[3], 'category':row[0]})
                        

                
                if len(row) == 6:
                    rows.append({'total': float(row[1]), '<1': row[2], '1-3': row[3], '3-5':row[4], '>5':row[5], 'category': row[0]})
                
                if len(row) == 7:
                    rows.append({'total': float(row[1]), '<1':row[2], '1-3':row[3] + row[4], '3-5': row[5], '>5': row[6], 'category': row[0]})
                if len(row) == 8:
                    hdrs = get_table_headers(tbl)
                    total_idx = [idx for idx, s in enumerate(hdrs) if 'total' in s][0]
                    if total_idx > 3:
                        # Total is at the end of the table
                        rows.append({'total': int(row[7]), '<1':float(row[1]), '1-3':float(row[2]) + float(row[3]), '3-5': float(row[4]) + float(row[5]), '>5': row[6], 'category': row[0]})
                    else:
                        # Total is at the beginning of the table
                        rows.append({'total': float(row[1]), '<1':float(row[2]), '1-3':float(row[3]) + float(row[4]), '3-5': float(row[5]) + float(row[6]), '>5': row[7], 'category': row[0]})
            except:
                print("Unknown error!")
                pass
    return rows


def scrape_text_table(wholetext):
    idxs =  [a.start() for a in list(re.finditer('contractual', wholetext))]
    text_chunks = [wholetext[idx:idx+4000] for idx in idxs]
    chunk_scores = np.zeros(len(text_chunks))
    keywords = ['contractual obligations', 'long-term debt', 'operating leases']
    for i,text_chunk in enumerate(text_chunks):
        for word in keywords:
            if word in text_chunk:
                chunk_scores[i] += 1
    final_text_chunk = text_chunks[np.argmax(chunk_scores)]
    lines = final_text_chunk.split('\n')
    lines = [x for x in lines if (hasNumbers(x))]
    keywords = ['2005', '2006', '2007', '2008', '2009', 'thereafter', 'total']
    keywords = keywords + row_kws
    lines = [x for x in lines if (hasKeywords(x, keywords))]
    lines = [x.split(' ') for x in lines]
    for i, line in enumerate(lines):
        lines[i] = list(filter(lambda a: (a != '') and (a != '$') and (a !='<u>') and (a !='</u>'), line))    
    tbl_list = []
    entry = None
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
    return lines, tbl_list
    
    
def scrape_text_rows(lines, tbl_list):
    rows = []
    for row in tbl_list:
        if any([word in row[0] for word in row_kws]):
            if ('following' not in row[0]):
                rows.append(clean_row(row))

    row_dicts = []
    hdr = get_table_headers_from_list(lines)
    total_idx = [idx for idx, s in enumerate(hdr) if 'total' in s][0]
    if len(rows[0]) == 6:
        for row in rows:
            if total_idx < 3:
                row_dicts.append({'total': int(row[1]), '<1':row[2], '1-3':row[3], 
                             '3-5': row[4], '>5': row[5], 'category': row[0]})
            else:
                row_dicts.append({'total': int(row[5]), '<1':row[1], '1-3':row[2], 
                             '3-5': row[3], '>5': row[4], 'category': row[0]})
    elif len(rows[0]) == 8:
        for row in rows:
            if total_idx > 3:
                # Total is at the end of the table
                row_dicts.append({'total': int(row[7]), '<1':float(row[1]), '1-3':float(row[2]) + float(row[3]), 
                             '3-5': float(row[4]) + float(row[5]), '>5': row[6], 'category': row[0]})
            else:
                # Total is at the beginning of the table
                row_dicts.append({'total': float(row[1]), '<1':float(row[2]), '1-3':float(row[3]) + float(row[4]), 
                             '3-5': float(row[5]) + float(row[6]), '>5': row[7], 'category': row[0]})
    return(row_dicts)