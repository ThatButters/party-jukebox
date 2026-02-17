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

# Chat messages (kept in memory, last 100)
chat_messages = []
chat_lock = threading.Lock()
MAX_CHAT_MESSAGES = 100

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

        # Find Shorts video IDs to exclude them
        shorts_ids = set(re.findall(r'/shorts/([^"]{11})', html))

        # Combine results (take first 5, skip Shorts)
        seen_ids = set()
        for i in range(min(len(video_ids), 10)):
            vid = video_ids[i]
            if vid not in seen_ids and vid not in shorts_ids and len(results) < 5:
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
        
        # API: Get video info (title) via YouTube oEmbed
        elif parsed_path.path == '/api/video-info':
            query_params = parse_qs(parsed_path.query)
            video_id = query_params.get('id', [''])[0]
            if video_id:
                try:
                    from urllib.request import Request
                    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
                    req = Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urlopen(req, timeout=5) as resp:
                        info = json.loads(resp.read().decode('utf-8'))
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'title': info.get('title', 'Unknown')}).encode())
                except Exception:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'title': None}).encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No video ID provided'}).encode())
            return

        # API: Get chat messages (optionally after a given ID)
        elif parsed_path.path == '/api/chat':
            query_params = parse_qs(parsed_path.query)
            after_id = int(query_params.get('after', ['0'])[0])
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            with chat_lock:
                msgs = [m for m in chat_messages if m['id'] > after_id]
            self.wfile.write(json.dumps(msgs).encode())
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
        
        # API: Post a chat message
        elif parsed_path.path == '/api/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                name = data.get('name', 'Anonymous')[:20]
                text = data.get('text', '')[:500]
                if text.strip():
                    with chat_lock:
                        msg_id = int(time.time() * 1000)
                        chat_messages.append({
                            'id': msg_id,
                            'name': name,
                            'text': text.strip(),
                            'time': time.strftime('%H:%M')
                        })
                        # Trim to max
                        while len(chat_messages) > MAX_CHAT_MESSAGES:
                            chat_messages.pop(0)
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'success': True, 'id': msg_id}).encode())
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Empty message'}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
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
