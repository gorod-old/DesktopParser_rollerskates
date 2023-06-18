import os

import gspread
from FernetPack import del_f_file, get_f_file

from MessagePack.message import err_log


def get_spreadsheet(spreadsheet_id):
    """Get spreadsheet by Id"""
    json_file = get_f_file('GOOGLE_CREDENTIALS_KEY', 'json')
    gs = gspread.service_account(filename=json_file)
    sh = gs.open_by_key(spreadsheet_id)
    del_f_file('GOOGLE_CREDENTIALS_KEY', 'json')
    return sh


def get_worksheet(spreadsheet_id, sheet_id):
    """Get worksheet by Id"""
    sh = get_spreadsheet(spreadsheet_id)
    worksheet = sh.get_worksheet_by_id(sheet_id)
    return worksheet


def get_worksheet_by_title(spreadsheet_id, sheet_title):
    """Get worksheet by title"""
    sh = get_spreadsheet(spreadsheet_id)
    worksheet = sh.worksheet(sheet_title)
    return worksheet


def get_worksheet_by_index(spreadsheet_id, sheet_index):
    """Get worksheet by index"""
    sh = get_spreadsheet(spreadsheet_id)
    worksheet = sh.get_worksheet(sheet_index)
    return worksheet


def get_worksheet_id(spreadsheet_id, index):
    """Return worksheet id or None if index not exists"""
    sh = get_spreadsheet(spreadsheet_id)
    worksheet_list = sh.worksheets()
    if index < len(worksheet_list):
        return worksheet_list[index].id
    return None


def create_worksheet(spreadsheet_id, title, rows=100, cols=20, index=None):
    """Add new worksheet with title(title) and position(index)"""
    json_file = get_f_file('GOOGLE_CREDENTIALS_KEY', 'json')
    gs = gspread.service_account(filename=json_file)
    sh = gs.open_by_key(spreadsheet_id)
    worksheet = sh.add_worksheet(title=title, rows=rows, cols=cols, index=index)
    return worksheet


def update_sheet_data(data, header, spreadsheet_id, sheet_id):
    """Replace worksheet data"""
    try:
        sheet = get_worksheet(spreadsheet_id, sheet_id)
        sheet.clear()
        if header:
            sheet.update('A1', [header])
            sheet.update('A2', data)
        else:
            sheet.update('A1', data)
    except Exception as e:
        err_log('update_sheet_data', str(e))
        print(str(e))


def add_sheet_data(a1, data, spreadsheet_id, sheet_id):
    """Add worksheet data by a1 (top left corner)"""
    try:
        sheet = get_worksheet(spreadsheet_id, sheet_id)
        sheet.update(a1, data)
    except Exception as e:
        err_log('add_sheet_data', str(e))
        print(str(e))


def clear_worksheet_data(spreadsheet_id, sheet_id):
    """Clear worksheet data"""
    try:
        sheet = get_worksheet(spreadsheet_id, sheet_id)
        sheet.clear()
    except Exception as e:
        err_log('update_sheet_data', str(e))
        print(str(e))


def get_sheet_data_by_id(spreadsheet_id, sheet_id):
    """Get worksheet data as list[list]"""
    worksheet = get_worksheet(spreadsheet_id, sheet_id)
    data = worksheet.get_all_values()
    return data


def get_sheet_data_by_index(spreadsheet_id, index, dict_=False):
    """Get worksheet data as list[list]"""
    worksheet = get_worksheet_by_index(spreadsheet_id, index)
    data = worksheet.get_all_values() if not dict_ else worksheet.get_all_records()
    return data


def set_range_background(worksheet, a1, red, green, blue):
    """Set range (a1) background with red, green, blue values (float)"""
    worksheet.format(a1, {
        "backgroundColor": {
            "red": red,
            "green": green,
            "blue": blue
        }
    })
