from tkinter import Tk, Label, Button, Frame, messagebox
from json import load, dumps
from time import sleep, time
from threading import Thread

with open('soal.json', 'r') as file:
    file_soal = load(file)

class Session:
    def __init__(self, name, server):
        self.name = name
        self.server = server
        self.clients = {}
        self.scoreboard = {}
        self.quiz_state = 0

    def add_client(self, conn, name):
        if name in self.clients:
            conn.send('{ "data": false, "error": "Name has already been used" }'.encode("UTF-8"))
            conn.close()
        else:
            self.clients[conn] = name
            self.scoreboard[name] = 0
            print("User {name} terhubung dengan {session}".format(name= name, session=self.name))
            conn.send('{ "data": true, "error": null }'.encode("UTF-8"))

    def get_status(self):
        switcher = {
            0: ("Open", "DodgerBlue2", "Start"),
            1: ("Running", "limegreen", "Running"),
            2: ("Finished", "red2", "Delete")
        }

        return switcher.get(self.quiz_state)

    def bind_gui(self, master):
        self.session_frame = Frame(master)
        self.session_frame.pack()

        name_label = Label(self.session_frame, text = self.name)
        name_label.grid(row = 0, column = 0, sticky = "NSEW")

        self.session_frame.grid_columnconfigure(0, weight = 5)

        status_frame = Frame(self.session_frame)
        status_frame.grid(row = 0, column = 1, sticky = "NSEW")

        self.session_frame.grid_columnconfigure(0, weight = 2)

        label = self.get_status()

        self.status_label = Label(status_frame, text = label[0], fg = label[1])
        self.status_button = Button(status_frame, text = label[2], command = self.start_quiz)

        detail_button = Button(status_frame, text = "Status", command = self._show_status)

        self.status_label.grid(row = 0, column = 0, sticky = "NSEW")
        self.status_button.grid(row = 0, column = 1, sticky = "NSEW")
        detail_button.grid(row = 0, column = 2, sticky = "NSEW")

    def start_quiz(self):
        self.quiz_state = 1
        
        label = self.get_status()

        self.status_label["text"] = label[0]
        self.status_label["fg"] = label[1]
        self.status_button["text"] = label[2]
        self.status_button["fg"] = "light grey"
        self.status_button["state"] = "disabled"

        if len(self.clients) > 0:
            quiz_loop = Thread(target = self.begin_quiz_loop, daemon = True)
            quiz_loop.start()
        else:
            self.stop_quiz()

    def begin_quiz_loop(self):
        self.number = 0

        for conn in self.clients:
            conn.send('{ "data": "Quiz will start in 5 seconds. Prepare yourself, good luck!", "error": null }'.encode("UTF-8"))

        sleep(5)

        while self.number < len(file_soal):
            self.answers = {} # string-tuple = (jawaban, waktu)

            soal = {
                "soal": (file_soal[self.number]["soal"] + " (anda memiliki waktu 3 menit untuk menjawab)"),
                "pilihan": file_soal[self.number]["pilihan"]
            }
            
            print(self._format_to_json(soal)) # debug

            payload = self._format_to_json({
                "data": self._format_to_json(soal),
                "error": None
            }).encode("UTF-8")

            for conn in self.clients:
                conn.send(payload)

                listener = Thread(target=self.ask_answer, args=(conn,), daemon=True)
                listener.start()
                listener.join(5) # Ubah waktu untuk jawab disini

            self.update_scoreboard()
            self.post_scoreboard()

            sleep(3)

            self.number += 1
        
        result = "Kuis Selesai!\nPemenang dari kuis adalah: "
        winner = []

        for client in self.scoreboard:
            winner.append((client, self.scoreboard[client]))

        winner = sorted(winner, key=lambda x: x[1])

        result += winner[0][0] + " dengan skor " + str(winner[0][1])

        payload = self._format_to_json({
            "data": result,
            "error": None
        }).encode("UTF-8")

        for conn in self.clients:
            conn.send(payload)
        
        self.stop_quiz()

    def ask_answer(self, conn):
        while True:
            answer = conn.recv(1024).decode("UTF-8")

            client = self.clients[conn]

            if client in self.answers:
                conn.send('{ "data": None, "error": "You have already answered for this question!" }'.encode("UTF-8"))

            self.answers[client] = (answer, time())

    def update_scoreboard(self):
        answers = []

        for answer in self.answers:
            answers.append((self.answers[answer][0], self.answers[answer][1], answer))

        answers = sorted(answers, key=lambda x: x[1])

        cur_score = len(self.clients) + 1

        for answer in answers:
            if answer[0] == file_soal[self.number]["jawaban"]:
                self.scoreboard[answer[2]] += cur_score
                cur_score -= 1

    def post_scoreboard(self):
        announcements = "Jawaban benar: " + file_soal[self.number]["jawaban"] + ". "
        announcements += "Score saat ini:"

        winner = []

        for client in self.scoreboard:
            winner.append((client, self.scoreboard[client]))

        winner = sorted(winner, key=lambda x: x[1])

        for client in winner:
            announcements += "\n" + client[0] + ": " + str(client[1])

        announcements += "\nSoal selanjutnya dikirim dalam 3 detik lagi"
        announcements = announcements

        for conn in self.clients:
            verdict = ""
            name = self.clients[conn]

            if name in self.answers:
                verdict += "Jawaban anda: " + self.answers[name]
            else:
                verdict += "Anda tidak menjawab dalam batas waktu yang telah ditentukan"

            verdict += "\n"

            payload = self._format_to_json({
                "data": verdict + announcements,
                "error": None
            }).encode("UTF-8")

            conn.send(payload)

    def stop_quiz(self):
        self.quiz_state = 2

        label = self.get_status()
        self.status_label["text"] = label[0]
        self.status_label["fg"] = label[1]
        self.status_button["text"] = label[2]
        self.status_button["state"] = "normal"
        self.status_button["fg"] = "black"
        self.status_button["command"] = self.delete_session

    def delete_session(self):
        self.session_frame.destroy()
        self.server.delete_session(self.name)

    def _format_to_json(self, obj):
        return dumps(obj, indent=4)

    def _show_status(self):
        label = "Jumlah klien yang terhubung dengan sesi ini: " + str(len(self.scoreboard))

        if len(self.scoreboard) > 0:
            label += "\n"
            label = "Daftar klien beserta skor saat ini:"

            for client in self.scoreboard:
                label += "\n" + client + ": " + str(self.scoreboard[client])

        messagebox.showinfo("Current Status", label)
