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

def handle_ax25_connection(ax25_socket, telnet_host, telnet_port):
    """Handle AX.25 connection with menu system."""
    menu = b"""Welcome to the AX.25 Bridge

1. Connect to BBS
2. Local Commands

Choose an option: """
    try:
        ax25_socket.send(menu)
        data = ax25_socket.recv(1024)
        if not data:
            ax25_socket.close()
            return
        choice = data.strip().decode('ascii', errors='ignore').upper()
        
        if choice in ['1', 'BBS', 'CONNECT', 'C']:
            # Connect to BBS
            try:
                telnet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                telnet_socket.connect((telnet_host, telnet_port))
                print(f"AX.25 user connected to BBS")
                # Start forwarding
                ax25_to_telnet = threading.Thread(target=forward_data, args=(ax25_socket, telnet_socket))
                telnet_to_ax25 = threading.Thread(target=forward_data, args=(telnet_socket, ax25_socket))
                ax25_to_telnet.start()
                telnet_to_ax25.start()
                ax25_to_telnet.join()
                telnet_to_ax25.join()
            except Exception as e:
                ax25_socket.send(b"Failed to connect to BBS\n")
                print(f"Failed to connect to BBS: {e}")
            finally:
                ax25_socket.close()
                if 'telnet_socket' in locals():
                    telnet_socket.close()
                    
        elif choice in ['2', 'LOCAL', 'L']:
            # Local commands mode
            ax25_socket.send(b"Local mode. Type HELP for commands.\n")
            while True:
                ax25_socket.send(b"> ")
                try:
                    data = ax25_socket.recv(1024)
                    if not data:
                        break
                    cmd = data.strip().decode('ascii', errors='ignore').upper()
                    if cmd in ['HELP', 'H', '?']:
                        ax25_socket.send(b"Commands:\nHELP - Show this help\nSTATUS - Show bridge status\nBBS - Connect to BBS\nCONNECT <host>[:port] - Connect to any telnet server\nEXIT - Disconnect\n")
                    elif cmd in ['STATUS', 'S']:
                        ax25_socket.send(b"Bridge status: Running\nAX.25 interface active\n")
                    elif cmd in ['BBS', 'B']:
                        # Switch to BBS
                        try:
                            telnet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            telnet_socket.connect((telnet_host, telnet_port))
                            ax25_socket.send(b"Connecting to BBS...\n")
                            print(f"AX.25 user switched to BBS")
                            # Start forwarding
                            ax25_to_telnet = threading.Thread(target=forward_data, args=(ax25_socket, telnet_socket))
                            telnet_to_ax25 = threading.Thread(target=forward_data, args=(telnet_socket, ax25_socket))
                            ax25_to_telnet.start()
                            telnet_to_ax25.start()
                            ax25_to_telnet.join()
                            telnet_to_ax25.join()
                        except Exception as e:
                            ax25_socket.send(b"Failed to connect to BBS\n")
                            print(f"Failed to connect to BBS: {e}")
                        finally:
                            if 'telnet_socket' in locals():
                                telnet_socket.close()
                        break
                    elif cmd.startswith('CONNECT ') or cmd.startswith('C '):
                        # Connect to arbitrary telnet server
                        try:
                            # Parse host and port
                            connect_args = cmd[8:].strip() if cmd.startswith('CONNECT ') else cmd[2:].strip()
                            if ':' in connect_args:
                                host, port_str = connect_args.split(':', 1)
                                port = int(port_str)
                            else:
                                host = connect_args
                                port = 23
                            
                            if not host:
                                ax25_socket.send(b"Usage: CONNECT <host>[:port]\n")
                                continue
                            
                            telnet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            telnet_socket.connect((host, port))
                            ax25_socket.send(f"Connecting to {host}:{port}...\n".encode())
                            print(f"AX.25 user connected to {host}:{port}")
                            # Start forwarding
                            ax25_to_telnet = threading.Thread(target=forward_data, args=(ax25_socket, telnet_socket))
                            telnet_to_ax25 = threading.Thread(target=forward_data, args=(telnet_socket, ax25_socket))
                            ax25_to_telnet.start()
                            telnet_to_ax25.start()
                            ax25_to_telnet.join()
                            telnet_to_ax25.join()
                        except ValueError:
                            ax25_socket.send(b"Invalid port number. Use: CONNECT <host>[:port]\n")
                        except Exception as e:
                            ax25_socket.send(b"Failed to connect to specified server\n")
                            print(f"Failed to connect to {host}:{port}: {e}")
                        finally:
                            if 'telnet_socket' in locals():
                                telnet_socket.close()
                        break
                    elif cmd in ['EXIT', 'E', 'QUIT', 'Q']:
                        ax25_socket.send(b"Goodbye\n")
                        break
                    else:
                        ax25_socket.send(b"Unknown command. Type HELP for help.\n")
                except:
                    break
            ax25_socket.close()
        else:
            ax25_socket.send(b"Invalid choice. Disconnecting.\n")
            ax25_socket.close()
    except:
        ax25_socket.close()

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

            # Handle the connection with menu system
            threading.Thread(target=handle_ax25_connection, args=(conn, TELNET_HOST, TELNET_PORT)).start()

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        ax25_socket.close()

if __name__ == '__main__':
    main()