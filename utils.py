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
        data.append([ele for ele in cols if ele]) 
    return data


def most_likely_table(tables):
    # Given a list of tables, identify the most likely table to summarize contractual obligations
    if len(tables) == 1:
        return tables[0]
    
    table_scores = np.zeros(len(tables))
    keywords = ['obligations', 'lease', 'debt', 'operating', 'total', 'capital', 'long-term']
    
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
                  "supply","technology","truck","vehicle"]
        if len(row) == 0:
            continue
        if any(row_kw in row[0] for row_kw in row_kws):
            # TODO: accommodate tables with different than 6 rows
            # TODO: take care of nan categories
            # TODO: ensure that all the columns add up to 'total'
            # TODO: multiple by 1000 in case value reported < 100
            # TODO: remove $ signs
            if len(row) == 6:
                rows.append({'total': row[1], '<1': row[2], '1-3': row[3], '3-5':row[4], '>5':row[5], 'category': row[0]})
    return rows
