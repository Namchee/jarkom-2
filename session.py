from tkinter import Tk, Label, Button, Frame, messagebox
from json import load, dumps
from time import sleep, time
from threading import Thread
from random import shuffle
from copy import deepcopy

with open('soal.json', 'r') as file:
    file_soal = load(file)

class Session:
    def __init__(self, name, server):
        self.name = name
        self.server = server
        self.clients = {}
        self.scoreboard = {}
        self.quiz_state = 0
        self.is_accepting_answer = False

    def add_client(self, conn, name):
        if name in self.clients:
            conn.send('{ "data": false, "error": "Nama panggilan sudah dipakai oleh pengguna lain" }'.encode("UTF-8"))
            conn.close()
        else:
            self.clients[conn] = name
            self.scoreboard[name] = 0
            conn.send('{ "data": true, "error": null }'.encode("UTF-8"))

    def __get_status(self):
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

        label = self.__get_status()

        self.status_label = Label(status_frame, text = label[0], fg = label[1])
        self.status_button = Button(status_frame, text = label[2], command = self.__start_quiz)

        detail_button = Button(status_frame, text = "Status", command = self.__show_status)

        self.status_label.grid(row = 0, column = 0, sticky = "NSEW")
        self.status_button.grid(row = 0, column = 1, sticky = "NSEW")
        detail_button.grid(row = 0, column = 2, sticky = "NSEW")

    def __start_quiz(self):
        self.quiz_state = 1
        
        label = self.__get_status()

        self.status_label["text"] = label[0]
        self.status_label["fg"] = label[1]
        self.status_button["text"] = label[2]
        self.status_button["fg"] = "light grey"
        self.status_button["state"] = "disabled"

        if len(self.clients) > 0:
            quiz_loop = Thread(target = self.__begin_quiz_loop, daemon = True)
            quiz_loop.start()
        else:
            self.stop_quiz()

    def __begin_quiz_loop(self):
        self.number = 0

        for conn in self.clients:
            try:
                conn.send('{ "data": "Kuis akan dimulai dalam waktu 5 detik, selamat berjuang!", "error": null }'.encode("UTF-8"))
            except ConnectionResetError:
                name = self.clients[conn]
                del self.clients[conn]
                del self.scoreboard[name]

                if len(self.clients) == 0:
                    self.stop_quiz()
                    return

        sleep(5)

        self.session_soal = deepcopy(file_soal)

        shuffle(self.session_soal)

        while self.number < len(self.session_soal):
            self.is_accepting_answer = True
            self.answers = {} # string-tuple = (jawaban, waktu)

            soal = {
                "soal": self.session_soal[self.number]["soal"] + " (anda memiliki waktu 1 menit untuk menjawab)",
                "pilihan": self.session_soal[self.number]["pilihan"]
            }

            payload = self.__serialize({
                "data": self.__serialize(soal),
                "error": None
            }).encode("UTF-8")

            listeners = []

            for conn in self.clients:
                try:
                    conn.send(payload)

                    listener = Thread(target=self.__ask_answer, args=(conn,), daemon=True)
                    listeners.append(listener)
                except ConnectionResetError:
                    del self.clients[conn]
                    continue

            for listener in listeners:
                listener.start()

            sleep(60) # Ubah waktu disini

            self.is_accepting_answer = False
                
            self.__update_scoreboard()
            self.__post_scoreboard()

            sleep(3)

            self.number += 1
        
        result = "Kuis Selesai!\nPemenang dari kuis adalah: "
        winner = []

        for client in self.scoreboard:
            winner.append((client, self.scoreboard[client]))

        winner = sorted(winner, key=lambda x: x[1], reverse = True)

        result += winner[0][0] + " dengan skor " + str(winner[0][1])

        payload = self.__serialize({
            "data": result,
            "error": None
        }).encode("UTF-8")

        for conn in self.clients:
            conn.send(payload)
            conn.close()
        
        self.stop_quiz()

    def __ask_answer(self, conn):
        while self.is_accepting_answer == True:
            try:
                answer = conn.recv(1024).decode("UTF-8")

                client = self.clients[conn]

                if client in self.answers:
                    conn.send('{ "data": null, "error": "Anda telah menjawab untuk soal ini!" }'.encode("UTF-8"))

                self.answers[client] = (answer, time())
                break
            except ConnectionResetError:
                del self.clients[conn]
                continue

    def __update_scoreboard(self):
        answers = []

        for answer in self.answers:
            answers.append((self.answers[answer][0], self.answers[answer][1], answer))

        answers = sorted(answers, key=lambda x: x[1])

        cur_score = len(self.clients)

        for answer in answers:
            if answer[0].lower() == self.session_soal[self.number]["jawaban"].lower():
                self.scoreboard[answer[2]] += cur_score
                cur_score -= 1

    def __post_scoreboard(self):
        announcements = "Jawaban benar: " + self.session_soal[self.number]["jawaban"] + ".\n"
        announcements += "Score saat ini:"

        winner = []

        for client in self.scoreboard:
            winner.append((client, self.scoreboard[client]))

        winner = sorted(winner, key=lambda x: x[1], reverse = True)

        for client in winner:
            announcements += "\n" + client[0] + ": " + str(client[1])

        announcements += "\nSoal selanjutnya dikirim dalam 3 detik lagi"
        announcements = announcements

        for conn in self.clients:
            try:
                verdict = ""
                name = self.clients[conn]

                if name in self.answers:
                    verdict += "Jawaban anda: " + self.answers[name][0]
                else:
                    verdict += "Anda tidak menjawab dalam batas waktu yang telah ditentukan"

                verdict += "\n"

                payload = self.__serialize({
                    "data": verdict + announcements,
                    "error": None
                }).encode("UTF-8")

                conn.send(payload)
            except ConnectionResetError:
                del self.clients[conn]
                continue

    def stop_quiz(self):
        self.quiz_state = 2

        label = self.__get_status()
        self.status_label["text"] = label[0]
        self.status_label["fg"] = label[1]
        self.status_button["text"] = label[2]
        self.status_button["state"] = "normal"
        self.status_button["fg"] = "black"
        self.status_button["command"] = self.__delete_session

    def __delete_session(self):
        self.session_frame.destroy()
        self.server.delete_session(self.name)

    def __serialize(self, obj):
        return dumps(obj, indent=4)

    def __show_status(self):
        label = "Jumlah klien yang terhubung dengan sesi ini: " + str(len(self.scoreboard))

        if len(self.scoreboard) > 0:
            label += "\n"
            label = "Daftar klien beserta skor saat ini:"

            for client in self.scoreboard:
                label += "\n" + client + ": " + str(self.scoreboard[client])

        messagebox.showinfo("Current Status", label)
