import socket
from json import loads, dumps
from tkinter import Frame, Label, Entry, Button, messagebox, Tk, Toplevel, Message
from threading import Thread

host = "127.0.0.1" # localhost, self-isolate dude!
port = 8080

class ClientApp:
    def __init__(self, window):
        self.window = window
        self.__init_gui()
        self.__prompt_sname()

    def __init_gui(self):
        self.soal_label = Message(self.window, text = "Tunggu! Anda belum terkoneksi! Masukkan informasi mengenai sesi dan nama anda!", width = 360)
        self.soal_label.pack()

        self.pilihan_label = Message(self.window, text = "", anchor = "w", width = 360)
        self.pilihan_label.pack()

        self.pengumuman_label = Message(self.window, text = "", anchor = "w", width = 360)
        self.pengumuman_label.pack()

        self.grid = Frame(self.window, width = 360)
        self.grid.pack()

        jawaban_label = Label(self.grid, text = "Jawaban anda: ")
        
        self.jawaban_entry = Entry(self.grid, state = "disabled")
        self.sumbit_jawaban = Button(
            self.grid,
            text = "Jawab",
            state = "disabled"
        )

        jawaban_label.grid(row = 0, column = 0)
        self.jawaban_entry.grid(row = 0, column = 1)
        self.sumbit_jawaban.grid(row = 0, column = 2)

    def __prompt_sname(self):
        self.prompt = Toplevel(self.window)
        self.prompt.title("Masukan informasi koneksi")
        
        self.prompt.attributes("-topmost", 1)

        frame = Frame(self.prompt)
        frame.pack()

        session_label = Label(frame, text = "Nama Sesi: ", anchor = "w")
        self.session_entry = Entry(frame, width = 30)

        name_label = Label(frame, text = "Nama Panggilan: ", anchor = "w")
        self.name_entry = Entry(frame, width = 30)

        session_label.grid(row = 0, column = 0)
        self.session_entry.grid(row = 0, column = 1)

        name_label.grid(row = 1, column = 0)
        self.name_entry.grid(row = 1, column = 1)

        ok_button = Button(
            frame,
            text = "Submit",
            command = self.__connect_test
        )

        ok_button.grid(row = 2, column = 1)

        self.prompt.bind('<Return>', self.__handle_enter) # Bind enter key

    def __handle_enter(self, event):
        self.__connect_test()

    def __connect_test(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.conn.connect((host, port))

            s_name = self.session_entry.get()
            n = self.name_entry.get()

            if len(s_name) == 0:
                messagebox.showerror("Error", "Nama sesi tidak boleh kosong")
                return

            if len(n) == 0:
                messagebox.showerror("Error", "Nama panggilan tidak boleh kosong")
                return

            session_info = {
                "session": s_name,
                "name": n
            }

            self.conn.send(self.__serialize(session_info).encode("UTF-8"))

            reply = self.conn.recv(1024).decode("UTF-8")
            reply_obj = self.__deserialize(reply)

            if reply_obj["data"] == True:
                messagebox.showinfo("Koneksi berhasil", "Koneksi ke server " + s_name + " berhasil dengan nama " + n)
                self.soal_label["text"] = "Anda sudah terhubung ke sesi " + s_name + " dengan nama " + n + ". Tunggu aba-aba selanjutnya."
                self.prompt.destroy()
                listener = Thread(target = self.__listenr, daemon = True)
                listener.start()
            else:
                messagebox.showerror("Koneksi gagal", "Koneksi ke server " + s_name + " dengan nama " + n + " gagal karena " + reply_obj["error"])

        except ConnectionRefusedError:
            messagebox.showerror("Koneksi gagal dilakukan karena server tidak dapat dihubungi")

    def __serialize(self, obj):
        return dumps(obj, indent=4)

    def __deserialize(self, obj):
        return loads(obj)

    def __sajikan_soal(self, soal, pilihan):
        self.jawaban_entry["state"] = "normal"
        self.sumbit_jawaban["state"] = "normal"

        self.jawaban_entry.delete(0, 'end')

        self.pengumuman_label["text"] = ""
        self.soal_label["text"] = soal
        
        choices = ""

        for choice in pilihan:
            if len(choices) > 0:
                choices += ", "

            choices += choice

        choices = "Pilihan: " + choices

        self.pilihan_label["text"] = choices

        

        self.sumbit_jawaban["command"] = self.__submit_jawaban

        self.window.bind('<Return>', self.__handle_enter_when_soal)

    def __handle_enter_when_soal(self, event):
        self.window.unbind('<Return>')
        self.__submit_jawaban()

    def __submit_jawaban(self):
        self.conn.send(self.jawaban_entry.get().encode("UTF-8"))

        self.jawaban_entry["state"] = "disabled"
        self.sumbit_jawaban["state"] = "disabled"

        self.pengumuman_label["text"] = "Anda sudah menjawab untuk pertanyaan ini, tunggu hasilnya"

    def __listenr(self):
        while True:
            reply = self.conn.recv(1024).decode("UTF-8")
            reply_obj = self.__deserialize(reply)
            data = reply_obj["data"]

            if data[0] == '{': # Dapat soal
                data_obj = self.__deserialize(data)
                self.__sajikan_soal(data_obj["soal"], data_obj["pilihan"])
            elif data.startswith("Kuis akan"): # Notifikasi
                self.soal_label["text"] = data
            else: # Scoreboard
                self.jawaban_entry["state"] = "disabled"
                self.sumbit_jawaban["state"] = "disabled"
                self.pengumuman_label["text"] = data

                if data.startswith("Kuis Selesai"):
                    self.conn.close()
                    break

def main():
    window = Tk(className="WomQuiz Client")

    window.resizable(0, 0)

    window.geometry("360x360")
    app = ClientApp(window)

    window.mainloop()

if __name__ == "__main__":
    main()