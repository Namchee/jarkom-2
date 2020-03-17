import socket
import json

"""
    Ingat, payload dikirim dalam bentuk JSON! decode dengan json.loads()
"""
def main():
    host = "127.0.0.1"
    port = 8080

    conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    conn.connect((host, port))

    conn.send('{ "session": "test", "name": "Namchee" }'.encode("UTF-8"))

    res = conn.recv(1024)
    print(res.decode()) # Check koneksi, bila berhasil, maka "data" = true
    print(conn.recv(1024).decode()) # Kuis dimulai!

    while res.strip() != 'END':
        res=conn.recv(1024) # terima soal, print
        result=res.decode()
        qdata=json.loads(result["data"])
        qerr=json.loads(result["error"])
        if qerr is none:
            print("Tidak ada soal")
            break
        else:
            print(qdata)
            answer=input(" -> ")
            conn.send(answer.encode())
    
    #menerima scoreboard jawaban
    res=conn.recv(1024)
    result=res.decode()
    qdata=json.loads(result["data"])
    qerr=json.loads(result["error"])
    if qerr is none:
        print("Jawaban anda tidak tercatat")
    else:
        print(qdata)
    
    #menerima scoreboard winner
    res=conn.recv(1024)
    result=res.decode()
    qdata=json.loads(result["data"])
    qerr=json.loads(result["error"])
    if qerr is none:
        print("Scoreboard tidak bisa ditampilkan")
    else:
        print(qdata)

    conn.close() # Ini gak usah dipikirin dulu

"""
    while True:
        res = conn.recv(1024)
        if not res:
            break
        print(res.decode())
"""     
        
        
if __name__ == "__main__":
    main()