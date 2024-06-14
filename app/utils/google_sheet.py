import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread_formatting import *
# Path to the JSON credential file
ss_cred_path = 'data/json/chatbotgamefi-a0dcf41e5bcd.json' 

# Define the scope
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'] 

# Add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name(ss_cred_path, scope) 

# Authorize the client sheet 
gc = gspread.authorize(creds) 

# Open the spreadsheet by ID
spreadsheet_id = "1BDbCJLfXUjFDT-a-t2av4iVL-S1t2osQdNN4458iXNM"
wks = gc.open_by_key(spreadsheet_id)

# Select the worksheet
worksheet = wks.worksheet('report')

# Define the format for the 'Chưa đọc' cell (making it orange with border)
orange_format = CellFormat(
    backgroundColor=Color(1, 0.6, 0),  # orange background
    textFormat=TextFormat(bold=True, foregroundColor=Color(0, 0, 0)),
    borders=Borders(
        left=Border("SOLID", Color(0, 0, 0)),
        right=Border("SOLID", Color(0, 0, 0)),
        top=Border("SOLID", Color(0, 0, 0)),
        bottom=Border("SOLID", Color(0, 0, 0))
    )
)

# Define the format for other cells (you can customize as needed, with border)
blue_format = CellFormat(
    backgroundColor=Color(0.7, 0.85, 1),  # light blue background
    textFormat=TextFormat(bold=False, foregroundColor=Color(0, 0, 0)),
    borders=Borders(
        left=Border("SOLID", Color(0, 0, 0)),
        right=Border("SOLID", Color(0, 0, 0)),
        top=Border("SOLID", Color(0, 0, 0)),
        bottom=Border("SOLID", Color(0, 0, 0))
    )
)
async def create_new_report(report: list):
    report.append("Chưa đọc")
    worksheet.insert_row(report, 2)
    format_cell_range(worksheet, 'A2:A2', blue_format)  # Format cell A2
    format_cell_range(worksheet, 'B2:B2', blue_format)  # Format cell B2
    format_cell_range(worksheet, 'C2:C2', blue_format)  # Format cell C2
    format_cell_range(worksheet, 'D2:D2', blue_format)  # Format cell D2
    format_cell_range(worksheet, 'E2:E2', blue_format)  # Format cell E2
    format_cell_range(worksheet, 'F2:F2', blue_format)  # Format cell F2
    format_cell_range(worksheet, 'G2:G2', blue_format)  # Format cell G2
    format_cell_range(worksheet, 'H2:H2', blue_format)  # Format cell H2
    format_cell_range(worksheet, 'I2:I2', orange_format)  # Format cell H2