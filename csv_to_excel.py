import pandas as pd
import sys

def csv_to_excel(csv_filename, excel_filename=None):
    if not excel_filename:
        excel_filename = csv_filename
    if '.xlsx' not in excel_filename:
    	excel_filename = excel_filename + ".xlsx"
    writer = pd.ExcelWriter(excel_filename, engine='xlsxwriter')
    csv_df = pd.read_csv(csv_filename)
    csv_df.to_excel(writer, sheet_name='Sheet1')
    writer.save()

    print("Converted csv to excel file, saved at: ", excel_filename)

if len(sys.argv) == 3:  
    csv_to_excel(sys.argv[1], sys.argv[2])
else:
    print("Not enough arguments; are you running `python csv_to_excel.py <csv_file_name> <excel_file_name>`?")
