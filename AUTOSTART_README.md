# StudyCoach Auto-Start Configuration

This directory contains scripts and configuration files to set up StudyCoach for automatic startup.

## Quick Start

1. **Setup auto-start scripts:**
   ```bash
   ./scripts/setup_autostart.sh
   ```

2. **Start StudyCoach:**
   ```bash
   ./scripts/autostart.sh
   ```

3. **Check status:**
   ```bash
   ./scripts/status.sh
   ```

4. **Stop StudyCoach:**
   ```bash
   ./scripts/stop.sh
   ```

## Auto-Start Methods

### Method 1: Simple Script-Based Auto-Start
Use the provided scripts for basic auto-start functionality:

- `scripts/autostart.sh` - Starts StudyCoach in the background
- `scripts/stop.sh` - Stops the running StudyCoach instance
- `scripts/status.sh` - Check if StudyCoach is running
- `scripts/setup_autostart.sh` - Initial setup script

### Method 2: GitHub Codespaces Auto-Start
For GitHub Codespaces, automatically start StudyCoach when the codespace opens:

1. **Setup codespace auto-start:**
   ```bash
   ./scripts/setup_codespace_autostart.sh
   ```

2. **Disable codespace auto-start:**
   ```bash
   ./scripts/disable_codespace_autostart.sh
   ```

When enabled, StudyCoach will automatically start whenever you open the codespace and be available at:
`https://CODESPACE_NAME-5000.app.github.dev`

### Method 3: Systemd Service (Production Recommended)
For production servers, use the systemd service:

1. **Install the service:**
   ```bash
   sudo cp studycoach.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable studycoach
   ```

2. **Start the service:**
   ```bash
   sudo systemctl start studycoach
   ```

3. **Check service status:**
   ```bash
   sudo systemctl status studycoach
   ```

4. **View logs:**
   ```bash
   sudo journalctl -u studycoach -f
   ```

### Method 4: Boot-time Auto-Start
To start StudyCoach automatically when the system boots:

#### Option A: Using crontab (user-level)
```bash
crontab -e
# Add this line:
@reboot /path/to/Hackathon-Project/scripts/autostart.sh
```

#### Option B: Using systemd (system-level)
Use Method 2 above - the systemd service will automatically start on boot.

## Configuration Notes

### Environment Setup
- Ensure your `.env` file is properly configured with Azure OpenAI credentials
- The virtual environment should be created and dependencies installed
- Scripts will automatically create a `logs/` directory for log files

### Port Configuration
- Default port: 5000
- The application will be accessible at `http://localhost:5000`
- To change the port, modify `app.py` line with `app.run()`

### User Permissions
- For systemd service, the default user is `www-data`
- You may need to adjust the user in `studycoach.service` based on your system
- Scripts create a PID file to track the running process

## Troubleshooting

### Common Issues

1. **Permission denied:**
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Virtual environment issues:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Port already in use:**
   - Check if StudyCoach is already running: `./scripts/status.sh`
   - Stop existing instance: `./scripts/stop.sh`
   - Check for other processes using port 5000: `lsof -i :5000`

4. **Missing .env file:**
   - Copy `.env.example` to `.env`
   - Configure your Azure OpenAI credentials

### Log Files
- Script logs: `logs/studycoach.log`
- Systemd logs: `sudo journalctl -u studycoach`

## Security Considerations

- Ensure your `.env` file has appropriate permissions (600)
- Consider using a reverse proxy (nginx/apache) for production
- The systemd service runs as `www-data` user for security
- Regular log rotation may be needed for long-running instances
