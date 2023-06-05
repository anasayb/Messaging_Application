
import socket
import mysql.connector
import threading
import pickle


# Network Configuration
PORT_NUM = 8022
temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
temp.connect(('8.8.8.8', 53))
SERVER_IP = temp.getsockname()[0]
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind((SERVER_IP, PORT_NUM))
HEADER_SIZE = 1024
FORMAT = "utf-8"
DISCONNECT = "!DISCONNECT!"
clientsConenctions = {}

# Databasr Configuratin
try:
    dbconnections = mysql.connector.connect(host="localhost", user="root", passwd="", database="chattingapplication")
except mysql.connector.Error as e:
    print(e)
    exit(0)
cursor = dbconnections.cursor()
query = "SELECT * FROM `users`;"
cursor.execute(query)
Users = cursor.fetchall()
cursor.close()


# This method is used to start the lestining in the server
def start(SERVER):
    SERVER.listen()
    print(f"Listenning on {SERVER_IP} ...")
    con = 0
    while True:
        connection, clientAddress = SERVER.accept()
        thread = threading.Thread(target= client_handle, args = (connection, clientAddress))
        thread.start()
        #print(f"[ACTIVE CONNECTION] {threading.active_count()-1}")
        con += 1
        if con == 20:
            break

# Recive Method
def rcv_msg(connection):
    info ={}    
    msg_length = connection.recv(HEADER_SIZE).decode(FORMAT)
    if msg_length:
        size = int(msg_length)
        info = connection.recv(size)     
    return info

# Sending Method
def send(clientCon ,message):
    msg_length = len(message)
    length_encoded = str(msg_length).encode(FORMAT)
    length_encoded += b' ' * ( HEADER_SIZE - len(length_encoded))
    clientCon.send(length_encoded)
    clientCon.send(message)


# Check credential
def login(connection, info):

    temp_cursor = dbconnections.cursor()
    query = f'SELECT `username`, `password` FROM users WHERE `username`="{info[0]}" AND `password`="{info[1]}"'
    temp_cursor.execute(query)

    test = temp_cursor.fetchall()
    temp_cursor.close()
    if not len(test) == 0:
        return True
    else:
        return False


# Add new user
def singUp(connection, info):
    

    temp_cursor = dbconnections.cursor()
    try:
        query = f'INSERT INTO `users` (`username`, `password`, `email`) VALUES ("{info[0]}", "{info[1]}", "{info[2]}");'
        temp_cursor.execute(query)
        dbconnections.commit()
        temp_cursor.close()
        return True
    except mysql.connector.IntegrityError:
        temp_cursor.close()
        return False


def getAllUsers():

    temp_cursor = dbconnections.cursor()
    query = f'SELECT `username` FROM users;'
    temp_cursor.execute(query)

    test = temp_cursor.fetchall();
    temp_cursor.close()
    return [i[0] for i in test]

# This method handle the connection after accepting it in a seperate thread 
def client_handle(connection, clientAdress):

    action = rcv_msg(connection).decode(FORMAT)
    info  = rcv_msg(connection)
    info = pickle.loads(info)

    if action == "Sign-Up":
        succeed = singUp(connection, info)
        if not succeed:
            send(connection, "Failed".encode(FORMAT))
            connection.close()
            return
        
    elif action == "Login":
        succeed = login(connection, info)
        if not succeed:
            send(connection, "Failed".encode(FORMAT))
            connection.close()
            return

    
    send(connection, "Logged".encode(FORMAT))
    username = info[0]
    
    send(connection, pickle.dumps(getAllUsers()))

    temp_cursor = dbconnections.cursor()
    query = f'SELECT `sender`,`receiver`, `message`, `date` FROM `messages` WHERE `sender`="{username}" OR `receiver`="{username}";'
    temp_cursor.execute(query)
    res = temp_cursor.fetchall()
    temp_cursor.close()
    
    send(connection, pickle.dumps(res))


    print(f"[NEW COONNECTION] {username}:{clientAdress} connected.")
    clientsConenctions[info[0]] = connection


    connected = True
    while connected:
        msg = pickle.loads(rcv_msg(connection))   
        if msg == DISCONNECT:
            connected = False
            send(clientsConenctions[username], pickle.dumps(DISCONNECT))
            print(f"[DISCONNECT] {username}:{clientAdress} has disconnected!")
            del clientsConenctions[username]
            
        else:           
            temp_cursor = dbconnections.cursor()
            query = f'INSERT INTO `messages` (`sender`, `receiver`, `message`, `date`) VALUES ("{msg[0]}", "{msg[1]}", "{msg[2]}", "{msg[3]}");'
            temp_cursor.execute(query)
            dbconnections.commit()
            temp_cursor.close()

            if msg[1] in clientsConenctions:
                send(clientsConenctions[msg[1]], pickle.dumps(msg))
           
    connection.close()



start(SERVER)
