# telnet-to-packet-bridge
AX.25 to Telnet Packet Bridge for Kali Linux

This project provides a two-way bridge between AX.25 packet connections from a Kantronics packet communicator and a telnet BBS at bbs.local.mesh.

## Features
- Listens for AX.25 connections on your callsign
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

4. The bridge will establish a telnet connection to the specified BBS and forward data bidirectionally.

## Configuration
The bridge is configured via command-line arguments:

- `--callsign`: Your AX.25 callsign (required)
- `--host`: Hostname of the telnet BBS (default: bbs.local.mesh)
- `--port`: Port of the telnet BBS (default: 23)
- `--interface`: AX.25 interface name (default: ax0)

## Notes
- This is a basic implementation.
- Ensure your AX.25 setup is correct and the BBS is reachable.
- For production use, consider security, error handling, and resource management.
- The bridge supports multiple concurrent AX.25 connections.
