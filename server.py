import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
gc = gspread.authorize(credentials)

# Your specific Google Sheet ID
SPREADSHEET_ID = '1iTFZbpKfGyMM88zAwuwA4ts53sVLl8krB1kn3hfl-9M'

# Security Variables
ALLOWED_ORIGIN = "https://drug-info.himanshul-k-dhanshal.workers.dev"
SECRET_API_KEY = "YourSuperSecretPassword123"

class RequestHandler(BaseHTTPRequestHandler):
    
    def _send_cors_headers(self):
        origin = self.headers.get('Origin')
        if origin == ALLOWED_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self._send_cors_headers()
        self.end_headers()

    def get_query_params(self):
        parsed_path = urllib.parse.urlparse(self.path)
        return urllib.parse.parse_qs(parsed_path.query)

    def is_authorized(self):
        params = self.get_query_params()
        if params.get('key', [None])[0] != SECRET_API_KEY:
            self.send_response(403)
            self._send_cors_headers()
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized Access Denied"}).encode('utf-8'))
            return False
        return True

    def do_GET(self):
        if not self.is_authorized(): return
        
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        try:
            spreadsheet = gc.open_by_key(SPREADSHEET_ID)
            
            # Fetch both relational tables
            molecules_sheet = spreadsheet.worksheet("drug_molecule")
            products_sheet = spreadsheet.worksheet("medicinal_product")
            
            m_data = molecules_sheet.get_all_records()
            p_data = products_sheet.get_all_records()
            
            # Attach structural row numbers
            for i, row in enumerate(m_data): row['_row_num'] = i + 2
            for i, row in enumerate(p_data): row['_row_num'] = i + 2
                
            # Package into a single JSON response
            response = json.dumps({
                "molecules": m_data,
                "inventory": p_data
            })
        except Exception as e:
            response = json.dumps({"error": str(e)})

        self.wfile.write(response.encode('utf-8'))

    def do_POST(self):
        if not self.is_authorized(): return
        params = self.get_query_params()
        sheet_name = params.get('sheet', ['medicinal_product'])[0]

        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            new_row_data = json.loads(post_data.decode('utf-8'))
            sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
            
            headers = sheet.row_values(1)
            row_values = [new_row_data.get(header, "") for header in headers]
            
            sheet.append_row(row_values)
            response = json.dumps({"success": True})
        except Exception as e:
            response = json.dumps({"error": str(e)})

        self.wfile.write(response.encode('utf-8'))

    def do_DELETE(self):
        if not self.is_authorized(): return
        params = self.get_query_params()
        sheet_name = params.get('sheet', ['medicinal_product'])[0]

        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        content_length = int(self.headers['Content-Length'])
        delete_data = self.rfile.read(content_length)

        try:
            data = json.loads(delete_data.decode('utf-8'))
            row_num = data.get('_row_num')
            if not row_num:
                raise ValueError("Row number is required for deletion")
            
            sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
            sheet.delete_rows(row_num)
            response = json.dumps({"success": True})
        except Exception as e:
            response = json.dumps({"error": str(e)})

        self.wfile.write(response.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting Pharma Relational API on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run()