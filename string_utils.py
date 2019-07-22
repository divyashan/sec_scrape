import re

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def hasKeywords(inputString, keywords):
    return any([word in inputString for word in keywords])

def get_cik(wholetext):
    # wholetext : txt file contents as a string
    # Returns central index key given text of SEC filing

    cikbase = re.search(r"CENTRAL INDEX KEY:\s*?\d{10}\b", wholetext, re.I).group()
    cik_re = re.split(r'\s', cikbase)[-1]        
    return cik_re

def get_datadate(wholetext):
    # wholetext : txt file contents as a string
    # Returns date of SEC filing given text 

    datadatebase = re.search(r"CONFORMED PERIOD OF REPORT:\s*?\d{8}\b", wholetext, re.I).group() 
    datadate_re = re.split(r'\s', datadatebase)[-1]  
    return datadate_re

def get_multiplier_from_string(text_chunk):
    thou_words = ['1000s', 'thousands', '$000s', "000s"]
    mil_words = ['1000000s', 'millions']
    bil_words = ['1000000000s', 'billions']
    
    if any([thou_word in text_chunk for thou_word in thou_words]):
        return 1000
    elif any([mil_word in text_chunk for mil_word in mil_words]):
        return 1000000
    elif any([bil_word in text_chunk for bil_word in bil_words]):
        return 1000000
    return 1

def clean_category_name(cname):
    cname = cname.replace('\n', '')
    cname = cname.replace('.', '')
    cname = ' '.join(cname.split())
    return cname
