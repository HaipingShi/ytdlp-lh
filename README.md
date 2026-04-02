# YT-DLP GUI for Windows

A modern, user-friendly Windows UI application for yt-dlp video downloader with excellent UX design.

## Features

- 🎥 **Easy Video Download**: Paste URL and download in 3 clicks
- 📺 **Quality Presets**: Best, 4K, 1080p, 720p, 480p, Audio Only
- 📝 **Batch Download**: Support playlists and multiple URLs
- 📊 **Progress Tracking**: Real-time progress bars, speed, ETA
- ⏸️ **Queue Management**: Pause, resume, reorder downloads
- 📚 **Download History**: Searchable history with redownload option
- 🔧 **Advanced Options**: Format selection, subtitles, metadata
- 🎨 **Modern UI**: Windows 11 Fluent Design with dark/light themes
- 🔄 **Auto-Updates**: Automatic updates for both app and yt-dlp

## Quick Start

### Prerequisites
- Windows 10 version 1809 or later
- .NET 8 Runtime (included in package)

### Installation

1. Download latest release from [Releases](https://github.com/user/ytdlp-gui/releases)
2. Run the MSIX installer
3. Launch "YT-DLP GUI" from Start Menu

### First Use

1. Copy a video URL from your browser
2. Paste it in the URL field
3. Select quality preset
4. Click "Download"

## Development

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
# Install Visual Studio 2022 with .NET 8 and Windows App SDK
# Open YtdlpGui.sln in Visual Studio
```

### Build from Source

```bash
# Backend
cd backend
pyinstaller --onefile --add-data "venv/Lib/site-packages/yt_dlp;yt_dlp" api/main.py

# Frontend
# Build in Visual Studio with Release configuration
```

## Architecture

```
ytdlp-gui/
├── backend/                 # Python backend
│   ├── api/                 # FastAPI application
│   ├── yt_dlp_service.py    # yt-dlp integration
│   ├── database.py          # SQLite operations
│   └── update_checker.py    # Update mechanism
├── frontend/                # WinUI 3 application
│   ├── Views/               # UI pages
│   ├── ViewModels/          # MVVM view models
│   ├── Services/            # Backend communication
│   └── App.xaml             # Application entry point
├── build/                   # Build configurations
└── docs/                    # Documentation
```

## User Flow Examples

### Download Single Video
1. Copy video URL from browser
2. Paste in URL field (Ctrl+V or right-click → Paste)
3. Select quality preset (e.g., "1080p")
4. Click "Download"
5. View progress in "Active Downloads" section
6. Click "Open Location" when complete

### Download Playlist
1. Copy playlist URL
2. Paste in URL field
3. Click "Fetch Playlist"
4. Review videos in playlist
5. Select/deselect videos as needed
6. Click "Add to Queue"
7. Go to Queue tab and click "Start All"

### Change Download Quality
1. Go to Settings tab
2. Under "Format Settings"
3. Change "Default Quality" dropdown
4. Click "Save Settings"
5. New setting applies to future downloads

## Configuration

Settings are stored in SQLite database at:
`%LOCALAPPDATA%\YT-DLP GUI\app.db`

### Output Template Variables

Available output template variables (expand for advanced users):
- `%(title)s` - Video title
- `%(id)s` - Video identifier
- `%(uploader)s` - Video uploader
- `%(ext)s` - File extension
- `%(format_id)s` - Format code
- And hundreds more...

See [yt-dlp documentation](https://github.com/yt-dlp/yt-dlp#output-template) for full list.

## Troubleshooting

### "URL is not supported" error
- Ensure internet connection is working
- Try updating yt-dlp: Settings → Check Now
- Some sites may require login or have restrictions

### Downloads are slow
- Check Settings → Network Settings → Speed Limit
- Try lower quality preset to reduce file size
- Consider using proxy if your ISP is throttling

### Video has no audio
- Select a format that includes both video and audio
- Check Settings → Format Settings → Prefer MP4 Format

### App won't start
- Ensure Windows 10 version 1809 or later
- Install Visual C++ Redistributables
- Check Event Viewer for detailed error logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Core download engine
- [WinUI 3](https://github.com/microsoft/microsoft-ui-xaml) - UI framework
- Community contributors and testers

## Support

- 📖 [Documentation](docs/user_guide.md) - Full user guide
- 🐛 [Issues](https://github.com/user/ytdlp-gui/issues) - Bug reports and feature requests
- 💬 [Discussions](https://github.com/user/ytdlp-gui/discussions) - General questions
