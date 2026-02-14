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
import time

# Ensure AX.25 module is loaded
os.system('modprobe ax25')

def status_monitor():
    """Monitor and display connection statistics."""
    while True:
        time.sleep(60)  # Update every minute
        uptime = time.time() - start_time
        print(f"Status: {active_connections} active, {total_connections} total connections, {uptime:.0f}s uptime")

# Start status monitoring thread
status_thread = threading.Thread(target=status_monitor, daemon=True)
status_thread.start()

def forward_data(source, destination):
    """Forward data from source to destination."""
    try:
        while True:
            data = source.recv(1024)
            if not data:
                break
            destination.sendall(data)  # Use sendall for reliability
    except (ConnectionResetError, BrokenPipeError, OSError):
        # Expected when connections close
        pass
    except Exception as e:
        print(f"Error in data forwarding: {e}")
        pass

def handle_ax25_connection(ax25_socket, telnet_host, telnet_port, user_callsign=None):
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
                telnet_socket.settimeout(30.0)  # 30 second timeout
                telnet_socket.connect((telnet_host, telnet_port))
                
                # Send user identification banner
                try:
                    peer_info = ax25_socket.getpeername()
                    if peer_info and len(peer_info) > 0:
                        user_id = f"[AX.25 Bridge - User: {peer_info[0]}]\r\n"
                        telnet_socket.send(user_id.encode('ascii', errors='ignore'))
                except:
                    telnet_socket.send(b"[AX.25 Bridge Connection]\r\n")
                
                print(f"AX.25 user connected to BBS")
                # Start forwarding
                ax25_to_telnet = threading.Thread(target=forward_data, args=(ax25_socket, telnet_socket), daemon=True)
                telnet_to_ax25 = threading.Thread(target=forward_data, args=(telnet_socket, ax25_socket), daemon=True)
                ax25_to_telnet.start()
                telnet_to_ax25.start()
                ax25_to_telnet.join()
                telnet_to_ax25.join()
            except socket.timeout:
                ax25_socket.send(b"Connection to BBS timed out\n")
                print(f"Connection to BBS timed out")
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
                        ax25_socket.send(b"Commands:\nHELP - Show this help\nSTATUS - Show bridge status\nBBS - Connect to BBS\nCONNECT <host>[:port] - Connect to any telnet server\nEXIT - Disconnect (requires confirmation)\n")
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
                            if not connect_args:
                                ax25_socket.send(b"Usage: CONNECT <host>[:port]\n")
                                continue
                            
                            # Basic validation
                            if len(connect_args) > 100:  # Prevent overly long input
                                ax25_socket.send(b"Host too long. Maximum 100 characters.\n")
                                continue
                            
                            if ':' in connect_args:
                                host, port_str = connect_args.split(':', 1)
                                try:
                                    port = int(port_str)
                                    if port < 1 or port > 65535:
                                        ax25_socket.send(b"Invalid port number. Must be 1-65535.\n")
                                        continue
                                except ValueError:
                                    ax25_socket.send(b"Invalid port number format.\n")
                                    continue
                            else:
                                host = connect_args
                                port = 23
                            
                            # Basic hostname validation
                            if not host or not all(c.isalnum() or c in '.-' for c in host):
                                ax25_socket.send(b"Invalid hostname format.\n")
                                continue
                            
                            telnet_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            telnet_socket.settimeout(30.0)  # 30 second timeout
                            telnet_socket.connect((host, port))
                            
                            # Send user identification banner
                            try:
                                peer_info = ax25_socket.getpeername()
                                if peer_info and len(peer_info) > 0:
                                    user_id = f"[AX.25 Bridge - User: {peer_info[0]} - Connecting to {host}:{port}]\r\n"
                                    telnet_socket.send(user_id.encode('ascii', errors='ignore'))
                            except:
                                telnet_socket.send(f"[AX.25 Bridge - Connecting to {host}:{port}]\r\n".encode())
                            
                            ax25_socket.send(f"Connecting to {host}:{port}...\n".encode())
                            print(f"AX.25 user connected to {host}:{port}")
                            # Start forwarding
                            ax25_to_telnet = threading.Thread(target=forward_data, args=(ax25_socket, telnet_socket), daemon=True)
                            telnet_to_ax25 = threading.Thread(target=forward_data, args=(telnet_socket, ax25_socket), daemon=True)
                            ax25_to_telnet.start()
                            telnet_to_ax25.start()
                            ax25_to_telnet.join()
                            telnet_to_ax25.join()
                        except socket.timeout:
                            ax25_socket.send(b"Connection timed out\n")
                        except socket.gaierror:
                            ax25_socket.send(b"Host not found\n")
                        except Exception as e:
                            ax25_socket.send(b"Failed to connect to specified server\n")
                            print(f"Failed to connect to {host}:{port}: {e}")
                        finally:
                            if 'telnet_socket' in locals():
                                telnet_socket.close()
                        break
                    elif cmd in ['EXIT', 'E', 'QUIT', 'Q']:
                        ax25_socket.send(b"Are you sure you want to exit the bridge? (y/n): ")
                        try:
                            confirm_data = ax25_socket.recv(1024)
                            if confirm_data:
                                confirm = confirm_data.strip().decode('ascii', errors='ignore').upper()
                                if confirm in ['Y', 'YES']:
                                    ax25_socket.send(b"Goodbye\n")
                                    break
                                else:
                                    ax25_socket.send(b"Exit cancelled.\n")
                            else:
                                ax25_socket.send(b"Exit cancelled.\n")
                        except:
                            ax25_socket.send(b"Exit cancelled.\n")
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
        ax25_socket.listen(50)  # Allow up to 50 pending connections
        print(f"Listening for AX.25 connections on callsign: {MY_CALL}")
        print(f"Telnet BBS: {TELNET_HOST}:{TELNET_PORT}")
        print(f"Max concurrent connections: {max_connections}")
    except Exception as e:
        print(f"Failed to set up AX.25 listener: {e}")
        sys.exit(1)

    try:
        while True:
            conn, addr = ax25_socket.accept()
            print(f"AX.25 connection from {addr}")
            
            # Update total connections counter
            global total_connections
            total_connections += 1
            
            # Check connection limit
            global active_connections
            if active_connections >= max_connections:
                conn.send(b"Bridge is at maximum capacity. Please try again later.\n")
                conn.close()
                continue
            
            active_connections += 1
            print(f"Active connections: {active_connections}/{max_connections}")

            # Handle the connection with menu system
            def connection_wrapper():
                global active_connections
                try:
                    handle_ax25_connection(conn, TELNET_HOST, TELNET_PORT)
                finally:
                    active_connections -= 1
                    print(f"Active connections: {active_connections}/{max_connections}")
            
            thread = threading.Thread(target=connection_wrapper, daemon=True)
            thread.start()

    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        ax25_socket.close()

if __name__ == '__main__':
    main()