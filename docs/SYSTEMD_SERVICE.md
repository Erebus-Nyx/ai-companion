# AI Companion Systemd Service Setup

This guide explains how to set up AI Companion as a systemd service that runs automatically on boot and in the background.

## Quick Setup

1. **Install the service:**
   ```bash
   ./scripts/install-systemd-service.sh
   ```

2. **Start the service:**
   ```bash
   ./scripts/service-manager.sh start
   ```

3. **Check status:**
   ```bash
   ./scripts/service-manager.sh status
   ```

## Important Notes

- **Development Mode**: The service runs with the `--dev` flag by default, which skips AI model validation at startup. This ensures reliable service startup even if some models are missing or corrupted.
- **Model Loading**: Models are loaded on-demand when features are used, not at startup.
- **Port**: The service runs on port 19443 by default.
- **Interface**: Access the Live2D interface at `http://localhost:19443/live2d`

## Service Management

### Using the Service Manager Script

The `service-manager.sh` script provides easy commands:

```bash
# Start the service
./scripts/service-manager.sh start

# Stop the service
./scripts/service-manager.sh stop

# Restart the service
./scripts/service-manager.sh restart

# Check service status
./scripts/service-manager.sh status

# View live logs
./scripts/service-manager.sh logs

# Enable auto-start on boot (done by default)
./scripts/service-manager.sh enable

# Disable auto-start on boot
./scripts/service-manager.sh disable

# Uninstall the service
./scripts/service-manager.sh uninstall
```

### Using Systemctl Directly

You can also use systemctl directly:

```bash
# Start service
systemctl --user start ai-companion

# Stop service
systemctl --user stop ai-companion

# Restart service
systemctl --user restart ai-companion

# Check status
systemctl --user status ai-companion

# View logs
journalctl --user -u ai-companion -f

# Enable auto-start
systemctl --user enable ai-companion

# Disable auto-start
systemctl --user disable ai-companion
```

## Service Configuration

### Default Settings

- **Port:** 19443
- **Host:** 0.0.0.0 (accessible from network)
- **User:** nyx
- **Working Directory:** /home/nyx/ai-companion
- **Auto-start:** Enabled on boot
- **Restart Policy:** Always restart on failure

### Service File Location

The service file is installed at:
```
~/.config/systemd/user/ai-companion.service
```

### Environment Variables

The service sets these environment variables:
- `AI_COMPANION_ENV=production`
- `AI_COMPANION_LOG_LEVEL=INFO`
- `PYTHONPATH=/home/nyx/ai-companion/src`

### Security Features

The service includes security hardening:
- **NoNewPrivileges:** Prevents privilege escalation
- **ProtectSystem:** Protects system directories
- **PrivateTmp:** Uses private /tmp directory
- **RestrictAddressFamilies:** Limits network access
- **Resource Limits:** Memory and CPU quotas

## Accessing the Service

Once running, you can access:

- **Main Interface:** http://localhost:19443
- **Live2D Avatar:** http://localhost:19443/live2d
- **API Endpoints:** http://localhost:19443/api/*

### Remote Access

To access from other machines on your network:
- **Main Interface:** http://YOUR_IP:19443
- **Live2D Avatar:** http://YOUR_IP:19443/live2d

Replace `YOUR_IP` with your machine's IP address.

## Logs and Monitoring

### View Logs

```bash
# Live logs (follow mode)
./scripts/service-manager.sh logs

# Or with journalctl
journalctl --user -u ai-companion -f

# View recent logs
journalctl --user -u ai-companion -n 50

# View logs since yesterday
journalctl --user -u ai-companion --since yesterday
```

### Log Locations

- **Systemd logs:** Available via `journalctl`
- **Application logs:** Stored in systemd journal
- **Model cache:** `~/.local/share/ai-companion/cache/`
- **Model storage:** `~/.local/share/ai-companion/models/`

## Troubleshooting

### Service Won't Start

1. **Check service status:**
   ```bash
   ./scripts/service-manager.sh status
   ```

2. **View error logs:**
   ```bash
   ./scripts/service-manager.sh logs
   ```

3. **Test manual start:**
   ```bash
   cd /home/nyx/ai-companion
   .venv/bin/ai-companion server --port 19443
   ```

### Permission Issues

If you see permission errors:

1. **Check file ownership:**
   ```bash
   ls -la /home/nyx/ai-companion
   ```

2. **Fix ownership if needed:**
   ```bash
   sudo chown -R nyx:nyx /home/nyx/ai-companion
   ```

3. **Check virtual environment:**
   ```bash
   ls -la /home/nyx/ai-companion/.venv/bin/ai-companion
   ```

### Port Already in Use

If port 19443 is already in use:

1. **Check what's using the port:**
   ```bash
   sudo netstat -tlnp | grep 19443
   ```

2. **Edit service file to use different port:**
   ```bash
   nano ~/.config/systemd/user/ai-companion.service
   ```
   
   Change the ExecStart line:
   ```ini
   ExecStart=/home/nyx/ai-companion/.venv/bin/ai-companion server --port 8080 --host 0.0.0.0
   ```

3. **Reload and restart:**
   ```bash
   systemctl --user daemon-reload
   ./scripts/service-manager.sh restart
   ```

### Models Not Loading

If models fail to load:

1. **Check model status:**
   ```bash
   .venv/bin/ai-companion models --list
   ```

2. **Check disk space:**
   ```bash
   df -h ~/.local/share/ai-companion
   ```

3. **Check model permissions:**
   ```bash
   ls -la ~/.local/share/ai-companion/models/
   ```

## Advanced Configuration

### Custom Service Configuration

To modify the service configuration:

1. **Edit the service file:**
   ```bash
   nano ~/.config/systemd/user/ai-companion.service
   ```

2. **Reload systemd:**
   ```bash
   systemctl --user daemon-reload
   ```

3. **Restart service:**
   ```bash
   ./scripts/service-manager.sh restart
   ```

### Environment Variables

Add custom environment variables to the service file:

```ini
[Service]
Environment=CUSTOM_VAR=value
Environment=ANOTHER_VAR=another_value
```

### Resource Limits

Adjust resource limits in the service file:

```ini
[Service]
MemoryMax=16G        # Maximum memory usage
CPUQuota=800%        # Maximum CPU usage (8 cores = 800%)
LimitNOFILE=131072   # Maximum open files
```

## Uninstalling

To completely remove the systemd service:

```bash
# Stop and uninstall service
./scripts/service-manager.sh uninstall

# Disable user lingering (optional)
sudo loginctl disable-linger nyx
```

## Security Considerations

### Network Security

- The service binds to `0.0.0.0:19443` by default (accessible from network)
- Consider using a firewall to restrict access
- For local-only access, change `--host 0.0.0.0` to `--host 127.0.0.1`

### File Permissions

- Service runs as user `nyx` (not root)
- Limited filesystem access via systemd security features
- Models stored in user's home directory

### Process Security

- No new privileges allowed
- Protected system directories
- Private temporary directory
- Restricted network address families

## Performance Tuning

### Memory Usage

- Default memory limit: 8GB
- Adjust based on your models and system RAM
- Monitor usage: `systemctl --user status ai-companion`

### CPU Usage

- Default CPU quota: 400% (4 cores)
- Adjust based on your system capabilities
- Monitor usage with `htop` or `systemctl --user status ai-companion`

### Model Optimization

- Use appropriate model sizes for your system
- Consider local git models for faster loading
- Enable fallback models for reliability
