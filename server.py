import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

credentials = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
gc = gspread.authorize(credentials)

SPREADSHEET_ID = '1iTFZbpKfGyMM88zAwuwA4ts53sVLl8krB1kn3hfl-9M'

# 1. Add your Cloudflare URL at the top of your file
ALLOWED_ORIGIN = "https://drug-info.himanshul-k-dhanshal.workers.dev"

class RequestHandler(BaseHTTPRequestHandler):
    # 2. Add this helper function to verify the origin
    def _send_cors_headers(self):
        origin = self.headers.get('Origin')
        # Only attach CORS headers IF the origin exactly matches your Cloudflare URL
        if origin == ALLOWED_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # 3. Add this function to handle browser "preflight" security checks
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        try:
            sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
            data = sheet.get_all_records()
            for index, row in enumerate(data):
                row['_row_num'] = index + 2 
            response = json.dumps(data)
        except Exception as e:
            response = json.dumps({"error": str(e)})

        self.wfile.write(response.encode('utf-8'))

    def do_POST(self):
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            new_row_data = json.loads(post_data.decode('utf-8'))
            sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
            row_values = list(new_row_data.values())
            sheet.append_row(row_values)
            response = json.dumps({"status": "success"})
        except Exception as e:
            response = json.dumps({"error": str(e)})

        self.wfile.write(response.encode('utf-8'))

    def do_PUT(self):
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        content_length = int(self.headers['Content-Length'])
        put_data = json.loads(self.rfile.read(content_length).decode('utf-8'))

        try:
            row_num = put_data.pop('_row_num')
            sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
            row_values = list(put_data.values())
            sheet.update(range_name=f'A{row_num}', values=[row_values])
            response = json.dumps({"status": "success"})
        except Exception as e:
            response = json.dumps({"error": str(e)})

        self.wfile.write(response.encode('utf-8'))

    def do_DELETE(self):
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        content_length = int(self.headers['Content-Length'])
        delete_data = json.loads(self.rfile.read(content_length).decode('utf-8'))

        try:
            row_num = delete_data.get('_row_num')
            sheet = gc.open_by_key(SPREADSHEET_ID).sheet1
            sheet.delete_rows(row_num)
            response = json.dumps({"status": "success"})
        except Exception as e:
            response = json.dumps({"error": str(e)})

        self.wfile.write(response.encode('utf-8'))

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting server on port {port}")
    httpd.serve_forever()

if __name__ == '__main__':
    run()