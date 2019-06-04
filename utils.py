import pandas as pd
from bs4 import BeautifulSoup
import numpy as np

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
    column_name_elim_words = [ 'amounts due by fiscal year']
    elim_subwords = ['\xa0','thousands']
    table_headers = [x.text for x in table.find_all('th')]
    if len(table_headers) == 0:
        table_headers = [x.text for x in table.find('tr').find_all('td')]
    table_headers = [x for x in table_headers if (x not in column_name_elim_words)]
    table_headers = [a.replace('\n', '') for a in table_headers]
    final_table_headers = []
    for header in table_headers:
        if not any(elim_word in header for elim_word in elim_subwords):
            final_table_headers.append(header)
    
    hdr_kws = ['2005', '2006', '2007', '2008', 'thereafter', 'total']
    tbl_list = table_to_list(table)
    for row in tbl_list:
        row_str = ' '.join(row)
        if any(hdr_kw in row_str for hdr_kw in hdr_kws):
            return row
    
    return final_table_headers

def most_likely_table(tables):
    # Given a list of tables, identify the most likely table to summarize contractual obligations
    if len(tables) == 1:
        return tables[0]
    
    table_scores = np.zeros(len(tables))
    keywords = ['obligations', 'lease', 'debt', 'operating', 'total', 'capital', 'long-term', 'payments', 'borrowings']
    
    for i, table in enumerate(tables):
        for word in keywords:
            if table.text.count(word) > 0:
                table_scores[i] += 1
    return tables[np.argmax(table_scores)]

def scrape_table(wholetext):
    # Given a piece of text, identify table most likely to summarize contractual obligations

    # Identify all tables
    parsed_html = BeautifulSoup(wholetext)
    tables = parsed_html.find_all('table')
    if len(tables) == 0:
        print("No tables!")
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
        row_kws = ["advertis","aircraft","build","buy","capacit","capex","capital","commercial","consult",
                  "clinical","collaborat","construct","consumer","customer","deliver","develop","distribut",
                  "drug","engineer","equipment","estate","exclusiv","expand","expansion","facility","facilities",
                  "factory","factories","fuel","hardware","infrastructur","innovat","invent","invest","joints+venture",
                  "land","license","licensing","manufactur","marketing","material","merchandis","operat","outsourc",
                  "patent","plant","procure","product","project","property","properties","purchas","research","research",
                  "R & D","right","royalt","science","scientist","sell","software","store","sponsor","storage","supplie",
                  "supply","technology","truck","vehicle", "transportation"]
        if len(row) == 0:
            continue
        row = [x for x in row if (x != '$')] # remove lone $ entries
        row = [a.replace('$', '') for a in row] 
        row = [a.replace(',', '') for a in row] 
        row = [x for x in row if (x != '')]
        row = [a.replace('\x97', '0') for a in row]
        row = [a.replace('\xa0', '') for a in row]
        if any(row_kw in row[0] for row_kw in row_kws):
            # TODO: accommodate tables with different than 6 rows
            # TODO: take care of nan categories
            # TODO: ensure that all the columns add up to 'total'
            # TODO: multiple by 1000 in case value reported < 100
            # TODO: remove $ signs
            
            try:
                if len(row) == 6:
                    rows.append({'total': float(row[1]), '<1': row[2], '1-3': row[3], '3-5':row[4], '>5':row[5], 'category': row[0]})
                if len(row) == 8:
                    hdrs = get_table_headers(tbl)
                    total_idx = hdrs.index('total')
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
