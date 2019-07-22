import numpy as np
import itertools
import six

from row_utils import *
from string_utils import *

def is_transposed(tbl_list):
    # True if any header keywords appear in first row
    first_col = [x[0] for x in tbl_list if (len(x) > 0)]
    n_hdr_kws = sum([any([hdr_kw in x for x in first_col]) for hdr_kw in HDR_KWS_WITHOUT_TOTAL])
    return (n_hdr_kws > 1)

def get_multiplier_from_preceding_text(table):
    prev_text = table.findAllPrevious(text=True)[:500]
    prev_text = [x.replace('\xa0', '') for x in prev_text]
    prev_text = [x.replace('\n', '') for x in prev_text]
    prev_text = [x.replace('$', '') for x in prev_text]
    prev_text = [x.replace(' ', '') for x in prev_text]
    prev_text = [x for x in prev_text if ('' != x)][:30]
    prev_text = ' '.join(prev_text)
    return get_multiplier_from_string(prev_text)

def get_multiplier_from_tbl_list(table_list):
    # table_list : list of lists representing table
    # Returns multiplier amount given list-type table in SEC filing

    table_string = ' '.join([' '.join(row) for row in table_list])
    return get_multiplier_from_string(table_string)

def get_multiplier_from_tbl(table):
    # table: BeautifulSoup table tag element
    # Returns multiplier ammount given HTML-type table in SEC filing
    
    # Look at table contents
    table_list = table_to_list(table)
    multiplier = get_multiplier_from_string(table.text)
    if multiplier > 1:
        return multiplier 
    
    multiplier = get_multiplier_from_tbl_list(table_list)
    if multiplier > 1:
        return multiplier
    
    # Look at preceding text
    multiplier = get_multiplier_from_preceding_text(table)
    if multiplier > 1:
        return multiplier
    
    # Look at preceding text
    n_prev_siblings = 6
    preceding_text = ' '.join([str(x) for x in itertools.islice(table.previous_siblings, n_prev_siblings)])
    thousands_idx = preceding_text.index('thousands') if 'thousands' in preceding_text else float('inf')
    millions_idx = preceding_text.index('millions') if 'millions' in preceding_text else float('inf')
    billions_idx = preceding_text.index('billions') if 'billions' in preceding_text else float('inf')
    
    # Return the appropriate multiplier based on the preceding text
    multipliers = [1000, 1000000, 1000000000]
    multiplier_idxs = [thousands_idx, millions_idx, billions_idx]
    if np.any([x < float('inf') for x in multiplier_idxs]):
        # Choose earliest occuring denomination
        return multipliers[np.argmin(multiplier_idxs)]
    
    # Check for non-plural forms
    thousand_idx = preceding_text.index('thousand') if 'thousand' in preceding_text else float('inf')
    million_idx = preceding_text.index('million') if 'million' in preceding_text else float('inf')
    billion_idx = preceding_text.index('billion') if 'billion' in preceding_text else float('inf')
    multiplier_idxs = [thousand_idx, million_idx, billion_idx]
    if np.any([x < float('inf') for x in multiplier_idxs]):
        # Choose earliest occuring denomination
        return multipliers[np.argmin(multiplier_idxs)]
    
    # Found no mention of alternate multipliers; default returns 1
    return 1


def transpose_list(tbl_list):
    # tbl_list : list-type table 
    # Given a list of lists, returns tranpose

    # Check there are more than 2 rows; if there aren't, we likely have the wrong table 
    if len(tbl_list) > 2:
        # If the length of the first or second row doesn't match the third,
        # adjust, such that the transpose preserves alignment
 
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

def consolidate_rows_in_tbl_list(tbl_list):
    new_tbl_list = []
    row_no = 0
    while row_no < len(tbl_list):
        if hasNumbers(' '.join(tbl_list[row_no])):
            new_tbl_list.append(tbl_list[row_no])
        elif row_no + 1 < len(tbl_list):
            new_tbl_list.append(tbl_list[row_no] + tbl_list[row_no + 1])
            row_no += 1
        row_no += 1

    return new_tbl_list

def table_to_list(table):
    # table : HTML-type table 
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
   
    # If table is transposed, return transposed list of lists 
    if is_transposed(data):
        data = transpose_list(data)
    data = combine_text_fields(data)
    # Combine entries that contain only text into one entry, 
    # e.g. 'purchase ', 'obligations' should be 'purchase obligations'
    # This is done to maintain alignment.
    data = consolidate_rows_in_tbl_list(data)
    data = combine_text_fields(data)
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
    for row in tbl_list:
        row_str = ' '.join(row)
        if any(hdr_kw in row_str for hdr_kw in HDR_KWS):
            return row

        
def combine_text_fields(lines):
    # lines : list of lists representing table entries 
    # Combine entries that contain only text into one entry, 
    # e.g. 'purchase ', 'obligations' should be 'purchase obligations'
    # This is done to maintain alignment.  
    
    tbl_list = []
    for i, line in enumerate(lines):
        new_line = []
        for j, word in enumerate(line):
            if (hasNumbers(word)) or ('-' in word) or ('\x97' in word):
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
    # tables : list of HTML-type tables 
    # Given a list of tables, identify the most likely table to summarize contractual obligations
    
    # If there's only one table in tables, only one most likely table!
    if len(tables) == 1:
        return tables[0]
    
    table_scores = np.zeros(len(tables))
    # Keywords used to rank the most likely table
    keywords = ['obligations', 'leases', 'debt', 'total', 'operating', 'capital', 'long-term', 'payments due', 'borrowings', 'long term', 'due by period', '2006-2007']
    
    # Counts number of keyword occurences in each table
    for i, table in enumerate(tables):
        for word in keywords:
            if table.text.count(word) > 0:
                table_scores[i] += 1

    # Identifies table with the highest score
    max_score = np.max(table_scores)
    max_idxs = np.where(table_scores == max_score)[0]

    # If there are no ties for the highest score, return winning table
    if len(max_idxs) == 1:
        return tables[max_idxs[0]]

    # If there is a tie, return the shortest table -- this is because massive tables often contain
    # all the relevant words, but are not the contractual obligations table
    else:
        min_length = float('inf')
        for idx in max_idxs:
            if len(tables[idx].text) < min_length:
                min_length_table = tables[idx]
                min_length = len(min_length_table.text)
        return min_length_table

def text_chunk_to_lines(text_chunk):
    # Takes in text chunk and returns trimmed lines
    l = text_chunk.split('\n')
    numbers_row_indices = [hasNumbers(x) for x in l]
    start_row_idx = np.where(np.array(numbers_row_indices) == True)[0][0]
    end_row_idx = np.where(np.array(numbers_row_indices) == True)[0][-1]
    
    lines = l[start_row_idx:end_row_idx+1]
    line_no = 0
    condensed_lines = []
    while line_no < len(lines):
        if hasNumbers(lines[line_no]):
            if line_no > 1 and not hasNumbers(lines[line_no-1]):
                condensed_lines.append(lines[line_no-1] + lines[line_no])
            else:
                condensed_lines.append(lines[line_no])
        line_no += 1

    lines = condensed_lines
    keywords = HDR_KWS + ROW_KWS
    lines = [x for x in lines if (hasKeywords(x, keywords))]
    lines = [x.split(' ') for x in lines]
    for i, line in enumerate(lines):
        lines[i] = list(filter(lambda a: (a != '') and (a != '$') 
                               and (a !='<u>') and (a !='</u>'), line))  
    return lines

def clean_tbl_list(tbl_list):
    new_tbl_list = []
    for row in tbl_list:
        row = [a.strip() for a in row]
        row = [re.sub("[\(\[].*?[\)\]]", "", a) for a in row]
        new_tbl_list.append(row)
    return new_tbl_list