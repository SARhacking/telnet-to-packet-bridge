#!/usr/bin/env python3
"""
AX.25 to Telnet Packet Bridge

This script creates a two-way bridge between AX.25 packet connections and a telnet BBS at bbs.local.mesh.
It listens for AX.25 connections on the configured callsign, and forwards data to/from a telnet connection to bbs.local.mesh.

Requirements:
- ax25-tools and ax25-apps installed
- AX.25 interface configured (e.g., ax0)
- Python 3

Usage:
python3 bridge.py --callsign YOUR_CALLSIGN [--host BBS_HOST] [--port BBS_PORT]
"""

import socket
import threading
import sys
import os
import argparse

# Ensure AX.25 module is loaded
os.system('modprobe ax25')

def forward_data(source, destination):
    """Forward data from source to destination."""
    try:
        while True:
            data = source.recv(1024)
            if not data:
                break
            destination.send(data)
    except:
        pass

def handle_ax25_connection(ax25_socket, telnet_socket):
    """Handle data forwarding for an AX.25 connection."""
    ax25_to_telnet = threading.Thread(target=forward_data, args=(ax25_socket, telnet_socket))
    telnet_to_ax25 = threading.Thread(target=forward_data, args=(telnet_socket, ax25_socket))

    ax25_to_telnet.start()
    telnet_to_ax25.start()

    ax25_to_telnet.join()
    telnet_to_ax25.join()

    ax25_socket.close()
    telnet_socket.close()

def main():
    parser = argparse.ArgumentParser(description='AX.25 to Telnet Bridge')
    parser.add_argument('--callsign', required=True, help='Your AX.25 callsign')
    parser.add_argument('--host', default='bbs.local.mesh', help='Telnet BBS hostname (default: bbs.local.mesh)')
    parser.add_argument('--port', type=int, default=23, help='Telnet BBS port (default: 23)')
    parser.add_argument('--interface', default='ax0', help='AX.25 interface name (default: ax0)')

    args = parser.parse_args()

    TELNET_HOST = args.host
    TELNET_PORT = args.port
    MY_CALL = args.callsign.upper()  # Ensure uppercase
    AX25_INTERFACE = args.interface

    # Set up AX.25 listener
    try:
        AF_AX25 = 3  # AX.25 address family
        ax25_socket = socket.socket(AF_AX25, socket.SOCK_SEQPACKET, 0)
        ax25_socket.bind((MY_CALL, 0))
        ax25_socket.listen(10)  # Allow up to 10 pending connections
        print(f"Listening for AX.25 connections on callsign: {MY_CALL}")
        print(f"Telnet BBS: {TELNET_HOST}:{TELNET_PORT}")
    except Exception as e:
        print(f"Failed to set up AX.25 listener: {e}")
        sys.exit(1)

    try:
        while True:
            conn, addr = ax25_socket.accept()
            print(f"AX.25 connection from {addr}")

            # Establish telnet connection to BBS
            try:
                telnet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                telnet_socket.connect((TELNET_HOST, TELNET_PORT))
                print(f"Connected to telnet BBS: {TELNET_HOST}:{TELNET_PORT}")
            except Exception as e:
                print(f"Failed to connect to telnet BBS: {e}")
                conn.close()
                continue

            # Handle the bridge in a separate thread for concurrency
            threading.Thread(target=handle_ax25_connection, args=(conn, telnet_socket)).start()

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        ax25_socket.close()

if __name__ == '__main__':
    main()