import socket
import json

UDP_IP = "127.0.0.1"
UDP_PORT = 3000

def send_udp_message():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    while True:
        message = input("Enter JSON message to send (or 'quit' to exit): ")
        if message.lower() == 'quit':
            break
        
        try:
            # Attempt to parse the input as JSON to validate it
            json.loads(message)
            
            # If parsing succeeds, send the message as is
            sock.sendto(message.encode('utf-8'), (UDP_IP, UDP_PORT))
            print(f"Message '{message}' sent to {UDP_IP}:{UDP_PORT}")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")

if __name__ == "__main__":
    send_udp_message()
