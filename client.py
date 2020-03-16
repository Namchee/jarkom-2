import socket

def main():
    host = "127.0.0.1"
    port = 8080

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((host, port))

    conn.send('{ "session": "test", "name": "Namchee" }'.encode("UTF-8"))

    res = conn.recv(1024)
    print(res.decode())

    while res.strip() != 'END':
        res=conn.recv(1024)
        answer=input(" -> ")
        conn.send(answer.encode())
        print(res.decode())

    client_socket.close()

"""
    while True:
        res = conn.recv(1024)
        if not res:
            break
        print(res.decode())
"""     
        
        
if __name__ == "__main__":
    main()