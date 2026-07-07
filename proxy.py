import socket
import ssl
import threading
import sys
import os
import urllib.parse
from ca import CertificateAuthority

# Configuration
PORT = 8080
HOST = "0.0.0.0"
REPLACEMENT_IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "local_images", "rax_logo.png"
)

# Load the replacement image content once at startup
try:
    with open(REPLACEMENT_IMAGE_PATH, "rb") as f:
        REPLACEMENT_IMAGE_DATA = f.read()
    print(f"[Proxy] Loaded replacement image ({len(REPLACEMENT_IMAGE_DATA)} bytes).")
except Exception as e:
    print(f"[Error] Failed to load replacement image from {REPLACEMENT_IMAGE_PATH}: {e}")
    sys.exit(1)

# Initialize Certificate Authority for on-the-fly SSL generation
ca = CertificateAuthority()

def handle_client(client_conn, client_addr):
    """Handles an individual client connection."""
    # Read the initial request line (e.g., "GET http://... HTTP/1.1" or "CONNECT example.com:443 HTTP/1.1")
    try:
        request_data = client_conn.recv(4096)
        if not request_data:
            client_conn.close()
            return
            
        # Parse the initial request
        header_end = request_data.find(b"\r\n\r\n")
        if header_end == -1:
            header_lines = request_data.split(b"\r\n")
        else:
            header_lines = request_data[:header_end].split(b"\r\n")
            
        request_line = header_lines[0].decode("utf-8", errors="ignore")
        parts = request_line.split()
        if len(parts) < 3:
            client_conn.close()
            return
            
        method, target, version = parts
        
        if method == "CONNECT":
            # HTTPS Proxy Tunneling Request
            # Target is "host:port" (e.g., "example.com:443")
            handle_https_tunnel(client_conn, target, client_addr)
        else:
            # Plain HTTP Request
            handle_http_request(client_conn, request_data, method, target, version, client_addr)
            
    except Exception as e:
        print(f"[Exception] Error handling client {client_addr}: {e}")
    finally:
        try:
            client_conn.close()
        except:
            pass

def handle_https_tunnel(client_conn, target, client_addr):
    """Establishes an SSL interception tunnel for HTTPS traffic using dynamic certs."""
    print(f"[Interception] Intercepting HTTPS connection to: {target}")
    
    # Split domain and port
    if ":" in target:
        domain, port_str = target.split(":")
        port = int(port_str)
    else:
        domain = target
        port = 443
        
    # Get or generate CA-signed certificate for the targeted domain
    try:
        cert_path, key_path = ca.get_certificate(domain)
    except Exception as e:
        print(f"[CA Error] Failed to generate certificate for {domain}: {e}")
        return
        
    # Respond to client with "HTTP/1.1 200 Connection Established"
    client_conn.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
    
    # Wrap client connection with SSL using the dynamic certificate
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    
    try:
        ssl_client_conn = context.wrap_socket(client_conn, server_side=True)
    except Exception as e:
        # Handshake fails if the browser/device doesn't trust our Root CA certificate
        print(f"[SSL Error] Handshake with client {client_addr} failed for {domain}: {e}")
        return
        
    try:
        # Read the encrypted request from the wrapper client socket
        decrypted_request = ssl_client_conn.recv(8192)
        if not decrypted_request:
            ssl_client_conn.close()
            return
            
        # Parse the inner HTTP request
        header_end = decrypted_request.find(b"\r\n\r\n")
        if header_end == -1:
            header_lines = decrypted_request.split(b"\r\n")
        else:
            header_lines = decrypted_request[:header_end].split(b"\r\n")
            
        request_line = header_lines[0].decode("utf-8", errors="ignore")
        parts = request_line.split()
        if len(parts) < 3:
            ssl_client_conn.close()
            return
            
        method, path, version = parts
        
        # Build raw request to send to destination server
        # Reconstruct headers to point directly to the domain
        # Also clean connection persistence to avoid persistent keep-alives that block simple reading
        raw_req_lines = []
        for line in header_lines[1:]:
            line_str = line.decode("utf-8", errors="ignore")
            if line_str.lower().startswith("connection:"):
                raw_req_lines.append("Connection: close")
            elif line_str.lower().startswith("proxy-connection:"):
                pass
            else:
                raw_req_lines.append(line_str)
                
        # If 'connection' wasn't set, force connection close to ease reading response
        if not any(l.lower().startswith("connection:") for l in raw_req_lines):
            raw_req_lines.append("Connection: close")
            
        rebuilt_headers = "\r\n".join(raw_req_lines)
        rebuilt_request = f"{method} {path} {version}\r\n{rebuilt_headers}\r\n\r\n".encode("utf-8")
        
        # If there's body content, append it
        if header_end != -1 and header_end + 4 < len(decrypted_request):
            rebuilt_request += decrypted_request[header_end + 4:]
            
        # Connect to original upstream server
        upstream_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssl_upstream_context = ssl.create_default_context()
        # Avoid verify errors in lab env if testing self-signed upstream endpoints
        ssl_upstream_context.check_hostname = False
        ssl_upstream_context.verify_mode = ssl.CERT_NONE
        
        ssl_upstream_conn = ssl_upstream_context.wrap_socket(upstream_socket, server_hostname=domain)
        ssl_upstream_conn.connect((domain, port))
        
        # Send reconstructed request
        ssl_upstream_conn.sendall(rebuilt_request)
        
        # Read entire upstream response
        response_bytes = bytearray()
        while True:
            chunk = ssl_upstream_conn.recv(8192)
            if not chunk:
                break
            response_bytes.extend(chunk)
            
        ssl_upstream_conn.close()
        
        # Process and potentially transform the response
        modified_response = process_response(response_bytes, path)
        
        # Send back to client
        ssl_client_conn.sendall(modified_response)
        
    except Exception as e:
        print(f"[Exception] HTTPS proxy error for {domain}: {e}")
    finally:
        try:
            ssl_client_conn.close()
        except:
            pass

def handle_http_request(client_conn, request_data, method, target, version, client_addr):
    """Handles unencrypted HTTP traffic by parsing target, forwarding to upstream, and replacing images."""
    print(f"[Interception] Intercepting HTTP request to: {target}")
    
    # Target can be a full URL: http://example.com/path
    parsed_url = urllib.parse.urlparse(target)
    domain = parsed_url.hostname
    port = parsed_url.port if parsed_url.port else 80
    path = parsed_url.path
    if parsed_url.query:
        path += "?" + parsed_url.query
        
    # Reconstruct headers and change Connection: keep-alive to Connection: close
    header_end = request_data.find(b"\r\n\r\n")
    if header_end == -1:
        header_lines = request_data.split(b"\r\n")
    else:
        header_lines = request_data[:header_end].split(b"\r\n")
        
    raw_req_lines = []
    for line in header_lines[1:]:
        line_str = line.decode("utf-8", errors="ignore")
        if line_str.lower().startswith("connection:"):
            raw_req_lines.append("Connection: close")
        elif line_str.lower().startswith("proxy-connection:"):
            pass
        else:
            raw_req_lines.append(line_str)
            
    if not any(l.lower().startswith("connection:") for l in raw_req_lines):
        raw_req_lines.append("Connection: close")
        
    rebuilt_headers = "\r\n".join(raw_req_lines)
    rebuilt_request = f"{method} {path} {version}\r\n{rebuilt_headers}\r\n\r\n".encode("utf-8")
    
    if header_end != -1 and header_end + 4 < len(request_data):
        rebuilt_request += request_data[header_end + 4:]
        
    try:
        # Connect to upstream HTTP server
        upstream_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        upstream_conn.connect((domain, port))
        upstream_conn.sendall(rebuilt_request)
        
        # Read the entire upstream response
        response_bytes = bytearray()
        while True:
            chunk = upstream_conn.recv(8192)
            if not chunk:
                break
            response_bytes.extend(chunk)
            
        upstream_conn.close()
        
        # Process and potentially transform the response
        modified_response = process_response(response_bytes, path)
        
        # Send back to client
        client_conn.sendall(modified_response)
        
    except Exception as e:
        print(f"[Exception] HTTP proxy error for {domain}: {e}")

def process_response(response_bytes, request_path):
    """
    Parses headers to identify image responses (by Content-Type or path extension).
    If matched, generates a modified response containing the local replacement image.
    """
    # Find the header boundary
    header_end = response_bytes.find(b"\r\n\r\n")
    if header_end == -1:
        # Malformed or empty response, return as is
        return response_bytes
        
    header_part = response_bytes[:header_end]
    body_part = response_bytes[header_end + 4:]
    
    header_lines = header_part.split(b"\r\n")
    status_line = header_lines[0]
    
    headers = {}
    for line in header_lines[1:]:
        if b":" in line:
            name, value = line.split(b":", 1)
            headers[bytes(name.strip().lower())] = bytes(value.strip())
            
    # Check if target resource is an image
    content_type = headers.get(b"content-type", b"").decode("utf-8", errors="ignore").lower()
    
    is_image = False
    
    # Match on Content-Type header
    if "image/" in content_type:
        is_image = True
        print(f"[Proxy Match] Intercepted image content-type: '{content_type}' for {request_path}")
    else:
        # Fallback check on URL extension
        lower_path = request_path.lower()
        if any(ext in lower_path for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"]):
            is_image = True
            print(f"[Proxy Match] Intercepted image file extension for: {request_path}")
            
    if is_image:
        print(f"[Substitution] Replacing image response for {request_path} with local copy.")
        
        # Create replacement HTTP Response Headers
        new_headers = []
        new_headers.append(b"HTTP/1.1 200 OK")
        new_headers.append(b"Content-Type: image/png")
        new_headers.append(f"Content-Length: {len(REPLACEMENT_IMAGE_DATA)}".encode("utf-8"))
        new_headers.append(b"Connection: close")
        new_headers.append(b"Cache-Control: no-store, no-cache, must-revalidate, max-age=0")
        new_headers.append(b"Pragma: no-cache")
        new_headers.append(b"Expires: 0")
        new_headers.append(b"Server: EduLabProxy/1.0")
        
        new_response = b"\r\n".join(new_headers) + b"\r\n\r\n" + REPLACEMENT_IMAGE_DATA
        return new_response
        
    # Not an image, return original response unmodified
    return response_bytes

def start_proxy():
    """Main loop to listen for incoming lab connections."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow socket address reuse to speed up restarts
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
    except Exception as e:
        print(f"[Error] Failed to bind to {HOST}:{PORT}: {e}")
        sys.exit(1)
        
    server.listen(100)
    print(f"==================================================")
    print(f"  EduLab Intercepting HTTP/HTTPS Proxy Running   ")
    print(f"  Listening on: {HOST}:{PORT}                      ")
    print(f"==================================================")
    print(f"Instruction: Install root CA certificate 'certs/ca.crt'")
    print(f"in your lab browser/device authority trust store.")
    print(f"Configure browser to use proxy at 127.0.0.1:{PORT}")
    print(f"--------------------------------------------------")
    
    try:
        while True:
            client_conn, client_addr = server.accept()
            # Handle client in a new thread for non-blocking concurrent requests
            t = threading.Thread(target=handle_client, args=(client_conn, client_addr))
            t.daemon = True
            t.start()
    except KeyboardInterrupt:
        print("\n[Proxy] Shutting down.")
    finally:
        server.close()

if __name__ == "__main__":
    start_proxy()
