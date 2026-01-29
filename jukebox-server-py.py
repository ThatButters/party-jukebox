#!/usr/bin/env python3
"""
Party Jukebox Server
Run this to start the jukebox with automatic IP detection.
Usage: python jukebox_server.py
"""

import http.server
import socketserver
import socket
import json
from urllib.parse import urlparse, parse_qs, quote
import threading
import time
from urllib.request import urlopen
from html.parser import HTMLParser

PORT = 8000

# Global state for the jukebox
jukebox_state = {
    'queue': [],
    'currentSong': None,
    'lastUpdate': time.time()
}
state_lock = threading.Lock()

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

def search_youtube(query):
    """Search YouTube using web scraping (no API key needed)"""
    try:
        # Use YouTube's search page
        search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
        
        # Set a user agent to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        from urllib.request import Request
        req = Request(search_url, headers=headers)
        
        with urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8')
        
        # Parse video IDs from the HTML
        results = []
        
        # Look for video IDs in the HTML (they appear in specific patterns)
        import re
        
        # Find all videoId entries in the ytInitialData JSON
        video_pattern = r'"videoId":"([^"]{11})"'
        title_pattern = r'"title":{"runs":\[{"text":"([^"]+)"}\]'
        channel_pattern = r'"ownerText":{"runs":\[{"text":"([^"]+)"'
        
        video_ids = re.findall(video_pattern, html)
        titles = re.findall(title_pattern, html)
        channels = re.findall(channel_pattern, html)
        
        # Combine results (take first 5)
        seen_ids = set()
        for i in range(min(len(video_ids), 10)):
            vid = video_ids[i]
            if vid not in seen_ids and len(results) < 5:
                seen_ids.add(vid)
                results.append({
                    'videoId': vid,
                    'title': titles[i] if i < len(titles) else 'Unknown Title',
                    'channelTitle': channels[i] if i < len(channels) else 'Unknown Channel',
                    'thumbnail': f'https://img.youtube.com/vi/{vid}/default.jpg'
                })
        
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return []

class JukeboxHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        # API: Get server IP
        if parsed_path.path == '/api/server-ip':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            ip_data = {
                'ip': get_local_ip(),
                'port': PORT
            }
            self.wfile.write(json.dumps(ip_data).encode())
            return
        
        # API: Get jukebox state
        elif parsed_path.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            with state_lock:
                self.wfile.write(json.dumps(jukebox_state).encode())
            return
        
        # API: Search YouTube
        elif parsed_path.path == '/api/search':
            query_params = parse_qs(parsed_path.query)
            query = query_params.get('q', [''])[0]
            
            if query:
                results = search_youtube(query)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(results).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No query provided'}).encode())
            return
        
        # Serve files normally
        super().do_GET()
    
    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        # API: Update jukebox state
        if parsed_path.path == '/api/state':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                new_state = json.loads(post_data.decode('utf-8'))
                
                with state_lock:
                    jukebox_state['queue'] = new_state.get('queue', [])
                    jukebox_state['currentSong'] = new_state.get('currentSong')
                    jukebox_state['lastUpdate'] = time.time()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': True}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())
            return
        
        # Default 404
        self.send_response(404)
        self.end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    local_ip = get_local_ip()
    
    with socketserver.TCPServer(("", PORT), JukeboxHandler) as httpd:
        print("=" * 60)
        print("🎵 Party Jukebox Server Started!")
        print("=" * 60)
        print(f"\n📱 Open on this computer:")
        print(f"   http://localhost:{PORT}/jukebox.html")
        print(f"\n📱 Share this URL for phones/other devices:")
        print(f"   http://{local_ip}:{PORT}/jukebox.html")
        print(f"\n💡 The QR code will automatically use: {local_ip}")
        print(f"\n🛑 Press Ctrl+C to stop the server")
        print("=" * 60)
        print()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Jukebox server stopped!")

if __name__ == "__main__":
    main()
