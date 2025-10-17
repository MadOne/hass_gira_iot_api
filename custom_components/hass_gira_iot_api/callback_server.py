import http.server
import socketserver
import json
from threading import Thread
from time import sleep

PORT = 8000


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])

        post_data = self.rfile.read(content_length)
        data = post_data.decode("utf-8")
        print(f"Received POST data: {post_data.decode('utf-8')}")

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        response_message = b"POST request received successfully!"
        self.wfile.write(response_message)


with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
    print(f"Serving at port {PORT}, ready to handle POST requests")
    httpd.serve_forever()
