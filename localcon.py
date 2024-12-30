# local_connection/main.py
import argparse
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import urllib.request
from pathlib import Path
from typing import Optional, Tuple
import socket

class LocalConnectionHandler:
    """Handler for local connection operations including hosting and downloading."""
    
    @staticmethod
    def get_local_ip() -> str:
        """Get local IP address of the machine."""
        try:
            # Create a socket to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    @staticmethod
    def start_server(fold_address: str, port: int, web_address: str, localhost_only: bool = False) -> None:
        """Start a local HTTP server with specified parameters."""
        try:
            # Change to the specified directory
            os.chdir(fold_address)
            
            # Custom handler to serve from specified web address
            class CustomHandler(SimpleHTTPRequestHandler):
                def translate_path(self, path):
                    # Remove the web_address prefix from the requested path
                    path = path.replace(web_address, '', 1)
                    return super().translate_path(path)
            
            # Bind to localhost or all interfaces
            host = 'localhost' if localhost_only else '0.0.0.0'
            server = HTTPServer((host, port), CustomHandler)
            
            # Get local IP for LAN access
            local_ip = LocalConnectionHandler.get_local_ip()
            
            print(f"\nServer started successfully!")
            print(f"Local access: http://localhost:{port}{web_address}")
            if not localhost_only:
                print(f"LAN access: http://{local_ip}:{port}{web_address}")
            print("\nPress Ctrl+C to stop the server")
            
            server.serve_forever()
            
        except PermissionError:
            print(f"Error: Permission denied accessing directory {fold_address}")
        except OSError as e:
            if e.errno == 98 or e.errno == 10048:  # Port already in use
                print(f"Error: Port {port} is already in use")
            else:
                print(f"Error: Could not start server - {str(e)}")
    
    @staticmethod
    def download_file(target_address: str, target_fold: str) -> None:
        """Download a file from target address to specified folder."""
        try:
            # Create target directory if it doesn't exist
            Path(target_fold).mkdir(parents=True, exist_ok=True)
            
            # Extract filename from URL
            filename = os.path.basename(target_address)
            if not filename:
                raise ValueError("Could not extract filename from URL")
            
            # Construct full path for downloaded file
            target_path = os.path.join(target_fold, filename)
            
            # Download the file
            urllib.request.urlretrieve(target_address, target_path)
            print(f"Successfully downloaded {filename} to {target_fold}")
            
        except urllib.error.URLError as e:
            print(f"Error: Could not download file - {str(e)}")
        except PermissionError:
            print(f"Error: Permission denied accessing directory {target_fold}")
        except ValueError as e:
            print(f"Error: {str(e)}")

def parse_arguments() -> Tuple[str, Optional[str], Optional[int], Optional[str], Optional[str], bool]:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Local Connection Tool")
    
    # Create mutually exclusive group for -s and -r options
    group = parser.add_mutually_exclusive_group(required=True)
    
    # Host mode arguments
    group.add_argument('-s', '--serve', nargs=3,
                      metavar=('fold_address', 'port', 'web_address'),
                      help='Start local server with specified folder, port, and web address')
    
    # Download mode arguments
    group.add_argument('-r', '--receive', nargs=2,
                      metavar=('target_address', 'target_fold'),
                      help='Download file from target address to specified folder')
    
    # Add localhost-only option
    parser.add_argument('--localhost-only', action='store_true',
                      help='Restrict server access to localhost only')
    
    args = parser.parse_args()
    
    # Process host mode arguments
    if args.serve:
        fold_address, port_str, web_address = args.serve
        try:
            port = int(port_str)
        except ValueError:
            print("Error: Port must be a number")
            sys.exit(1)
        return 'host', fold_address, port, web_address, None, args.localhost_only
    
    # Process receive mode arguments
    if args.receive:
        target_address, target_fold = args.receive
        return 'receive', None, None, target_address, target_fold, args.localhost_only
    
    return None, None, None, None, None, False

def main():
    """Main function to handle command line execution."""
    mode, fold_address, port, address, target_fold, localhost_only = parse_arguments()
    
    handler = LocalConnectionHandler()
    
    try:
        if mode == 'host':
            handler.start_server(fold_address, port, address, localhost_only)
        elif mode == 'receive':
            handler.download_file(address, target_fold)
    except KeyboardInterrupt:
        print("\nOperation terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()