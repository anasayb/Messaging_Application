# TODO: there is a problom that when ever recving a message the message will be displayed after the input promot, there are solutions but it requires the some sort of GUI implementaion (curses, tinker)
# TODO: use diffrente colors for diffrent users

import socket
import threading
import pickle
from datetime import datetime
from os import system, name
from colorama import Fore, init
from termcolor import colored

# Inizlizing the server info
SERVER_PORT = 8022
SERVER_ADDRESS = "192.168.1.31"
SERVER = (SERVER_ADDRESS, SERVER_PORT)
HEADER_SIZE = 1024
FORMAT = "utf-8"
current_chat = -1

# Disconnect message
DISCONNECT = "!DISCONNECT!"

# initilize the connection
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
username = ""

# This method is used to send any text massge to the server
def send(message):
    msg_length = len(message)
    length_encoded = str(msg_length).encode(FORMAT)
    length_encoded += b' ' * ( HEADER_SIZE - len(length_encoded))
    client.send(length_encoded)
    client.send(message)

# This method is used to recive other clients messge from the server
def recive():
    msg_length = client.recv(HEADER_SIZE).decode(FORMAT)
    if msg_length:
        msg_length = int(msg_length)
        msg = client.recv(msg_length)
        return msg
        

def clear():

    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')


# This method is used to inizilize the information between client and server after creating the connection
def inizilize():
    # connect to the server
    try:
        client.connect(SERVER)
    except Exception:
        print("Sorry the server is not Online. Please try again later.")
        exit()

    print("Welcom to chatApp!")
    choose = int(input("1- Login\n2- Sign-Up"))
    if choose == 1:
        username = input("Username: ")
        password = input("Password: ")

        send("Login".encode(FORMAT))
        send(pickle.dumps([username, password]))

        response = recive()
        if response.decode(FORMAT) == "Failed":
            print("Wrong username or password")
            exit(0)


    elif choose == 2:
        email = input("Email: ")
        username = input("Choose a Username: ")
        password = input("Password: ")

        send("Sign-Up".encode(FORMAT))
        send(pickle.dumps([username, password, email]))
        response = recive()
        if response.decode(FORMAT) == "Failed":
            print("Username already registred")
            exit(0)

    return username
    


def main_menu():

    global current_chat
    thread = threading.Thread(target= receive_and_update)
    thread.start()

    while True:
        print(f"{Fore.WHITE}Welcome")
        count = 1
        for user in users:
            if not user == username:
                print(f'{count}- {user.capitalize()}')
                count += 1

        print(f'{count}- Exit')
        
        current_chat = int(input("Choose a user: "))-1
        if current_chat == count-1:
            send(pickle.dumps(DISCONNECT))
            exit(0)

        show_massages(current_chat)
        current_chat = -1

    
def receive_and_update():

    while True:
        message  = pickle.loads(recive())
        if message == DISCONNECT:
            exit()
        messages[message[0]].append((message[0],message[2],message[3]))
        if not current_chat == -1:
            print(f'{Fore.RED}{message[2]} [{message[0]}]{Fore.GREEN}'.rjust(65))


def show_massages(current_chat):

    # claer the terminal
    clear()

    print(f'chatting with {users[current_chat]}. (To exit type "!BACK!")')
    #print(messages['test'])
    sorted_messages = sorted(messages[users[current_chat]], key=lambda x: datetime.strptime(str(x[2]), '%Y-%m-%d %H:%M:%S'))
    for message in sorted_messages:
        if(message[0] == username):
            print(colored(f'[ YOU ] {message[1]}', 'green'))
        else:
            print(f'{Fore.RED}{message[1]} [{message[0]}]'.rjust(65))


    init()
    msg = ""
    while True:
        msg = input(f"{Fore.GREEN}[ YOU ] ")
        if msg == "!BACK!":
            break
        info = [username, users[current_chat], msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        messages[users[current_chat]].append([username, msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        send(pickle.dumps(info))
    
    clear()






username = inizilize()
users = pickle.loads(recive())
users.remove(username)
data = pickle.loads(recive())


messages = dict.fromkeys(users)

for u in users:
    messages[u] = []

for message in data:

    if not (message[0] == username):
        (messages[message[0]]).append((message[0],message[2],message[3]))
    else:
        (messages[message[1]]).append((message[0],message[2],message[3]))


main_menu()


