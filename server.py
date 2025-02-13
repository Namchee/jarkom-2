import socket
import json
from threading import Thread
from tkinter import Tk, Button, Entry, Frame, messagebox
from session import Session

HOST = "127.0.0.1"
PORT = 8080

class ServerGUI:
    def __init__(self, master):
        self.master = master
        self.sessions = {}

        self.__construct_ui()

        self.server = Thread(target=self.__start_server, daemon=True)
        self.server.start()

    def __construct_ui(self):
        frame = Frame(self.master)
        frame.pack()

        self.session_name = Entry(
            frame,
            width = 30
        )
        add_btn = Button(
            frame,
            text="Add Quiz Session",
            command=self.__add_session
        )

        self.session_name.grid(row = 0, column = 0, sticky = "nsew")
        add_btn.grid(row = 0, column = 1, sticky = "nsew")

        self.master.bind('<Return>', self.__handle_enter) # Bind enter key

    def __handle_enter(self, event):
        self.__add_session()

    def __start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind((HOST, PORT))
            server.listen()

            while True:
                conn, _ = server.accept()
                stri = conn.recv(1024).decode()

                info = json.loads(stri)

                if info["session"] in self.sessions:
                    session = self.sessions[info["session"]]

                    if session.quiz_state == 1:
                        conn.send('{ "data": false, "error": "Kuis sudah dimulai, anda tidak boleh bergabung ditengah jalan" }'.encode("UTF-8"))
                        conn.close()
                    elif session.quiz_state == 2:
                        conn.send('{ "data": false, "error": "Kuis sudah selesai" }'.encode("UTF-8"))
                        conn.close()
                    else:
                        self.sessions[info["session"]].add_client(conn, info["name"])
                else:
                    conn.send('{ "data": false, "error": "Nama sesi yang anda minta tidak ada" }'.encode("UTF-8"))
                    conn.close()

    def __add_session(self):
        name = self.session_name.get()

        if len(name) == 0:
            messagebox.showerror("Error", "Nama sesi tidak boleh kosong")
            return

        if name in self.sessions:
            messagebox.showerror("Error", "Nama sesi sudah ada. Nama sesi tidak boleh duplikat")
            return
            
        self.sessions[name] = Session(name, self)
        self.session_name.delete(0, "end")
        self.session_name.select_clear()

        self.sessions[name].bind_gui(self.master)

    def delete_session(self, name):
        del self.sessions[name]

def main():
    window = Tk(className="WomQuiz")

    window.resizable(0, 0)
    app = ServerGUI(window)

    window.mainloop()

if __name__ == "__main__":
    main()
