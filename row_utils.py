
ROW_KWS = ["advertis","aircraft","build","buy","capacit","capex","capital","commercial","consult",
          "clinical","collaborat","construct","consumer","customer","deliver","develop","distribut",
          "drug","engineer","equipment","estate","exclusiv","expand","expansion","facility","facilities",
          "factory","factories","fuel","hardware","infrastructur","innovat","invent","invest","joints+venture",
          "land","license","licensing","manufactur","marketing","material","merchandis","operat","outsourc",
          "patent","plant","procure","product","project","property","properties","purchas","research","research",
          "R & D","right","royalt","science","scientist","sell","software","store","sponsor","storage","supplie",
          "supply","technology","truck","vehicle", "transportation", "obligations"]
HDR_KWS = ['2005', '2006', '2007', '2008', '2009', 'thereafter', 'total', '3-5', '1-3', 'than 1', 'than 5']
HDR_KWS_WITHOUT_TOTAL = ['2005', '2006', '2007', '2008', '2009', 'thereafter']

def pad_to_len(row, target_length):
    pad_length = target_length - len(row)
    row.extend(['0' for x in range(pad_length)])
    return row


def process_row_len_5(row, total_idx):
    row = pad_to_len(row, 5)
    if total_idx == -1:
         return {'<1':row[1], '1-3':row[2], '3-5':'-', '>5':row[3], 'category':row[0]}
    elif total_idx < 3:
        return {'total': float(row[1]), '<1':row[2], '1-3':row[3], '3-5':'-', '>5':row[4], 'category':row[0]}
    return {'total': float(row[4]), '<1':row[1], '1-3':row[2], '3-5':'-', '>5':row[3], 'category':row[0]}

def process_row_len_6(row, total_idx):
    row = pad_to_len(row, 6)
    if total_idx < 3:
        return {'total': float(row[1]), '<1': float(row[2]), '1-3': float(row[3]), '3-5':row[4], '>5':row[5], 'category': row[0]}
    return {'total': float(row[5]), '<1': float(row[1]), '1-3': row[2], '3-5':row[3], '>5':row[4], 'category': row[0]}

def process_row_len_7(row, total_idx):
    row = pad_to_len(row, 7)
    if total_idx == -1:
        return {'<1':row[1], '1-3':float(row[2]) + float(row[3]), '3-5': row[4], '>5': row[5], 'category': row[0]}
    elif total_idx < 3:
        return {'total': float(row[1]), '<1':row[2], '1-3':row[3] + row[4], '3-5': row[5], '>5': row[6], 'category': row[0]}
    return {'total': float(row[6]), '<1':row[1], '1-3':float(row[2]) + float(row[3]), '3-5': row[4], '>5': row[5], 'category': row[0]}

def process_row_len_8(row, total_idx):
    row = pad_to_len(row, 8)
    if total_idx > 3:
        return {'total': float(row[7]), '<1':float(row[1]), '1-3':float(row[2]) + float(row[3]), '3-5': float(row[4]) + float(row[5]), '>5': row[6], 'category': row[0]}
    return {'total': float(row[1]), '<1':float(row[2]), '1-3':float(row[3]) + float(row[4]), '3-5': float(row[5]) + float(row[6]), '>5': row[7], 'category': row[0]}

process_row_fn = {5: process_row_len_5, 6: process_row_len_6, 7: process_row_len_7, 8: process_row_len_8}

def process_row_longer(row, total_idx, hdrs):
    tafter = [idx for idx, s in enumerate(hdrs) if 'thereafter' in s]
    print('hdrs', hdrs)
    print('thereafter idx', tafter)
    if len(tafter) == 0:
        return None
    pruned_row = row[:tafter[0]+1]
    print("Pruned: ", pruned_row)
    if len(pruned_row) in process_row_fn.keys():
        return process_row_fn[len(pruned_row)](row, total_idx)
    else:
        return None
    
def clean_row(row):
    row = [x for x in row if (x != '$')] # remove lone $ entries
    row = [a.replace('$', '') for a in row] 
    row = [a.replace(',', '') for a in row] 
    row = [x for x in row if (x != '')]
    row = [a.replace('\x97', '0') for a in row]
    row = [a.replace('\xa0', '') for a in row]
    row = [a.replace('-', '0') for a in row]
    
    try: 
        float_attempt = [float(x) for x in row[1:]]
        return row
    except:
        print(row)
        return None