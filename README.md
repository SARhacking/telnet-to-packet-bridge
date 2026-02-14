# telnet-to-packet-bridge
AX.25 to Telnet Packet Bridge for Kali Linux

This project provides a two-way bridge between AX.25 packet connections from a Kantronics packet communicator and a telnet BBS at bbs.local.mesh.

## Features
- Listens for AX.25 connections on your callsign
- Presents a text-based menu to users upon connection
- Allows switching between BBS access and local commands
- Forwards data bidirectionally between AX.25 clients and the telnet BBS at bbs.local.mesh:23
- Supports multiple concurrent connections (up to 10 pending)

## Requirements
- Kali Linux
- ax25-tools and ax25-apps packages
- AX.25 interface configured (e.g., ax0)
- Python 3
- Access to bbs.local.mesh telnet BBS

## Installation
1. Install AX.25 tools:
   ```
   sudo apt update
   sudo apt install ax25-tools ax25-apps
   ```

2. Configure AX.25 interface (replace /dev/ttyUSB0 with your serial device connected to Kantronics TNC):
   ```
   sudo kissattach /dev/ttyUSB0 ax0
   sudo ifconfig ax0 up
   sudo axparms -setcall ax0 YOUR_CALLSIGN
   ```

3. Ensure the Kantronics TNC is in KISS mode and connected.

4. Clone or download this repository.

## Usage
1. Configure AX.25 interface (replace /dev/ttyUSB0 with your serial device connected to Kantronics TNC):
   ```
   sudo kissattach /dev/ttyUSB0 ax0
   sudo ifconfig ax0 up
   sudo axparms -setcall ax0 YOUR_CALLSIGN
   ```

2. Run the bridge with your callsign:
   ```
   python3 bridge.py --callsign YOUR_CALLSIGN
   ```

   Optional arguments:
   - `--host BBS_HOST`: Telnet BBS hostname (default: bbs.local.mesh)
   - `--port BBS_PORT`: Telnet BBS port (default: 23)
   - `--interface AX25_IF`: AX.25 interface name (default: ax0)

   Example:
   ```
   python3 bridge.py --callsign N0CALL --host bbs.example.com --port 8023
   ```

3. From your packet communicator, connect to your callsign (e.g., using AX.25 commands to connect to YOUR_CALLSIGN).

4. The bridge will present a text menu allowing users to choose between connecting to the BBS or accessing local commands.

## Menu System
When users connect via AX.25, they are presented with a text menu:

```
Welcome to the AX.25 Bridge

1. Connect to BBS
2. Local Commands

Choose an option:
```

### BBS Mode
- Connects the user directly to the telnet BBS
- Full bidirectional data forwarding

### Local Commands Mode
Available commands:
- `HELP` - Show available commands
- `STATUS` - Show bridge status
- `BBS` - Switch to BBS connection
- `CONNECT <host>[:port]` - Connect to any telnet server (default port 23)
- `EXIT` - Disconnect

Users can switch between modes at any time.

## Running on Startup
To automatically start the bridge when the system boots:

1. Copy the service file:
   ```
   sudo cp ax25-bridge.service /etc/systemd/system/
   ```

2. Edit the service file to set your callsign and any other parameters:
   ```
   sudo nano /etc/systemd/system/ax25-bridge.service
   ```
   Update the `ExecStart` line with your callsign and desired options.

3. Reload systemd and enable the service:
   ```
   sudo systemctl daemon-reload
   sudo systemctl enable ax25-bridge
   ```

4. Start the service:
   ```
   sudo systemctl start ax25-bridge
   ```

5. Check status:
   ```
   sudo systemctl status ax25-bridge
   ```

6. View logs:
   ```
   sudo journalctl -u ax25-bridge -f
   ```

The service will automatically restart if it crashes and start on boot.
