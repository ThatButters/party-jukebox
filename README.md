# Party Jukebox

A collaborative music player application designed for parties and group gatherings. Party Jukebox allows multiple people to queue songs from their phones that play on a central display, creating a shared music experience powered by YouTube.

## Features

### Main Display
- **YouTube Video Player**: Full-screen video playback with embedded controls
- **Live Queue Display**: Real-time view of upcoming songs with position numbers
- **QR Code Access**: Auto-generated QR code for easy mobile access
- **Retro Design**: Aesthetic jukebox interface with neon effects and animations
- **Auto-Play Queue**: Automatically plays next song when current video ends

### Mobile/Client Interface
- **YouTube Search**: Search for songs directly by name
- **Direct URL Support**: Add songs by pasting YouTube URLs
- **Real-time Sync**: Queue updates appear instantly across all devices
- **Simple Add-Only Mode**: Streamlined interface optimized for phone screens

## Quick Start

### Prerequisites
- Python 3.x (no additional packages required)
- Modern web browser
- All devices must be on the same local network

### Running the Server

1. Clone this repository:
```bash
git clone https://github.com/YOUR_USERNAME/party-jukebox.git
cd party-jukebox
```

2. Start the server:
```bash
python jukebox-server-py.py
```

3. The server will display:
```
Starting Party Jukebox Server...
Main Display: http://localhost:8000/jukebox.html
Network URL: http://192.168.x.x:8000/jukebox.html
Server IP: 192.168.x.x
Server is running on port 8000...
```

4. Open the **Main Display URL** on your computer/TV browser
5. Scan the QR code with phones or manually navigate to the **Network URL**

## Usage

### For the Host (Main Display)
1. Run the Python server on your computer
2. Open the displayed localhost URL in a web browser
3. Optionally fullscreen the browser (F11) for best display
4. Songs will auto-play as guests add them to the queue

### For Guests (Mobile Devices)
1. Scan the QR code displayed on the main screen
2. Click the "Add Song" button
3. Either:
   - **Search**: Type song name and select from results
   - **Direct URL**: Paste a YouTube link and click "Add Song"
4. Your song appears in the queue on all devices
5. Watch the main display to see when your song plays

## Technical Details

### Architecture
- **Backend**: Python HTTP server with built-in libraries only
- **Frontend**: Vanilla HTML5 + JavaScript (ES6)
- **Music Source**: YouTube (embedded player)
- **Sync Method**: REST API with 2-second polling interval

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/server-ip` | GET | Returns server IP and port |
| `/api/state` | GET | Returns current queue and playing song |
| `/api/state` | POST | Updates queue and current song |
| `/api/search` | GET | Searches YouTube (query param: `q`) |
| `/jukebox.html` | GET | Serves the main HTML file |

### State Management
- Shared state dictionary with thread-safe locking
- Queue array with song objects (id, title, addedBy)
- Current song tracking with YouTube video ID
- Automatic synchronization across all connected clients

### Security Features
- HTML escaping for XSS protection
- Thread-safe state management
- CORS headers for cross-origin requests
- Input validation for YouTube URLs

## File Structure

```
party-jukebox/
├── jukebox-server-py.py    # Python backend server (7.2 KB)
├── jukebox.html            # HTML5 frontend application (40.7 KB)
└── README.md               # This file
```

## How It Works

1. **Server Initialization**: Python server starts and detects local IP address
2. **Main Display**: Host opens jukebox.html in browser, sees empty player
3. **Mobile Connection**: Guests scan QR code or enter network URL
4. **Song Addition**: Guests search or paste YouTube URLs to add songs
5. **Queue Sync**: All devices poll server every 2 seconds for state updates
6. **Auto-Play**: Main display automatically plays first queued song
7. **Auto-Skip**: When video ends, next song in queue starts automatically

## Customization

### Change Server Port
Edit `jukebox-server-py.py` line where port is defined:
```python
PORT = 8000  # Change to your preferred port
```

### Modify Sync Interval
Edit `jukebox.html` polling interval:
```javascript
setInterval(syncState, 2000);  // Change 2000 to desired milliseconds
```

## Requirements

### Backend (Python)
- Python 3.x
- Built-in libraries only: `http.server`, `socket`, `json`, `urllib`, `threading`, `re`
- No pip packages required

### Frontend (Browser)
- Modern web browser with ES6 support
- External libraries loaded from CDN:
  - QRCode.js (v1.0.0) - QR code generation
  - YouTube IFrame API - Video embedding

### Network
- All devices on same local network
- Port 8000 accessible (or custom port if modified)

## Troubleshooting

**Cannot connect from mobile devices:**
- Ensure all devices are on the same WiFi network
- Check firewall settings allow connections on port 8000
- Verify the IP address shown by the server matches your network

**Songs not playing:**
- Ensure browser allows autoplay (may need user interaction first)
- Check YouTube video is not restricted or region-locked
- Verify internet connection is stable

**Queue not syncing:**
- Check browser console for errors
- Ensure JavaScript is enabled
- Try refreshing the page

## Use Cases

- House parties and gatherings
- Office break rooms
- Waiting rooms and lounges
- Wedding receptions
- College dorm common areas
- Coffee shops and cafes
- Retail stores with customer engagement

## License

This project is open source and available for personal and commercial use.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to improve the project.
