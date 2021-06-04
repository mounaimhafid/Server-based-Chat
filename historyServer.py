import socket
import select
import sys
import threading
import re
from history import Record
import time
import json
# Object which represents a server
ClientIDandIP = Record()
data = ""
destClientID = 0
senderClientID = 0
historyData = ""
class ChatServer:
    def __init__(self):
        print ('INITIALIZING SERVER CLASS')
        self.welcomingPort = 8844
        self.listOfClientIDs = []
        self.onlineSockets = {'1':None, '2':None, '3':None, '4':None, '5':None,
                              '6':None, '7':None, '8':None, '9':None, '10':None}
        self.onlineSessions = {'-99to-98' :None}
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind((socket.gethostname(), self.welcomingPort))
        self.listen_socket.listen(5)

    
    def send(self,data,clientSocket):
        clientSocket.send(data.encode())
    def receive(self, clientSocket):  
        return clientSocket.recv(2048).decode()

    def acceptConnection(self):
        clientInfo = self.listen_socket.accept()
        return clientInfo
        
def getSessionID(ses1,ses2):
    if int(ses1) < int(ses2):
        return str(ses1) + '-' + str(ses2)

    return str(ses2) + '-' + str(ses1)

def connectClient(server, clientInfo):
    
    print('client thread spawned!')
    #GET CLIENT SOCKET
    clientSocket = clientInfo[0]
    #GET CLIENT ADDRESS AND PORT NUMBER
    client_address_port = clientInfo[1]
    #GET CLIENT IP ADDRESS
    client_address = str(client_address_port[0])
    #SEND CONNECTED MESSAGE TO CLIENT
    server.send('CONNECTED',clientSocket)
    #GET CLIENT ID FROM CLIENT
    clientID = server.receive(clientSocket)[6]
    #ADD CLIENT ID AND IP ADDRESS TO DICTIONARY
    ClientIDandIP.addMessage(clientID, client_address)
    #PRINT NEW CLIENT LIST WHEN CLIENT IS ADDED
    print("Client List")
    ClientIDandIP.print()
    #ADD ONLINE SOCKET TO LIST
    server.onlineSockets[clientID] = clientSocket
    #get chat request from client

    #HOLDS DESTINATION CLIENT ID SO THAT IT IS SHARED BETWEEN CLIENTS
    global destClientID
    inChatMode = False
    
    #GET CLIENT COMMAND
    client_command = server.receive(clientSocket)
    
    #IF STATEMENT FOR CLIENT MAKING CHAT REQUEST
    if re.match(r"CHAT-REQUEST [0-9]+ from [0-9]+", client_command):
        #GET 
        destClientID = client_command[13]
        global senderClientID
        senderClientID = client_command[20]
        time.sleep(10)
        #print(senderClientID + " to " + destClientID)
        destClientResponse = server.receive(clientSocket)
        print('destClientResponse = ' + destClientResponse)
        if destClientResponse == 'APPROVED RECV':
            inChatMode = True
    #IF USER CHOOSES TO WAIT
    elif client_command == "WAITING":
        print(clientID + " is waiting")
        time.sleep(10)
        print (clientID + " stopped waiting")
        #IF THE USER IS BEING CHAT REQUESTED
        if clientID == destClientID:
            #TELL THE CLIENT
            server.send("CHAT-REQUESTED from " + senderClientID , clientSocket)
            #GET CLIENT RESPONSE
            clientResponse = server.receive(clientSocket)
            #IF USER CHOOSES TO ACCEPT CHAT REQUEST 
            if clientResponse == 'ACCEPTED':
                #TELL THE CHAT REQUEST SENDER CLIENT THAT THEIR RQUEST HAS BEEN APPROVED
                server.send('APPROVED', server.onlineSockets[senderClientID])
                inChatMode = True
    #IF USERS BEGIN A CHAT SESSION
    if inChatMode == True:
        #SLEEP SO THAT USERS CAN SYNC
        time.sleep(5)
        destSocket = server.onlineSockets[destClientID]
        server.onlineSessions[getSessionID(clientID, destClientID)] = 'Active'

        #IF YOU ARE THE ORIGINATOR 
        if clientID != destClientID:
            print('Client {0} initiated chat with client {1}'.format(clientID,destClientID))
            OtoSmsgThread = threading.Thread(target=OtoSmsgfowarding, args=(server, clientID, destClientID))
            OtoSmsgThread.start()
            
        #BEGIN LISTENING FOR MESSAGES FROM THE ORIGINATOR TO THE DESTINATION
        while True:
            #KEEP LISTENING FOR MESSAGES
            msgFromO = server.receive(clientSocket)
            sessionID = getSessionID(clientID,destClientID) # Session ID of the chat
            data = sessionID + " from:" + clientID + " " + msgFromO + "\n"
            #write to JSON history messages
            with open('data.json', 'w') as outfile:
                json.dump(data, outfile)            
            
            if "CHAT" in msgFromO:
                msgFromO = msgFromO.split(',')[1][:-1] # CHAT (sessionID,This is the message)
            elif "END_REQUEST" in msgFromO:
                print("a sent end notif")
                server.onlineSessions[getSessionID(clientID, destClientID)] = None
                server.send("END_NOTIF ({0})".format(getSessionID(clientID, destClientID)), clientSocket)
                server.send("END_NOTIF ({0})".format(getSessionID(clientID, destClientID)), destSocket)
                break
            
            #PRINT MESSAGE TO SERVER
            print(clientID + ": " + msgFromO)
            
            #FORWARD MESSAGE TO DESTINATION
            if msgFromO != "":
                server.send(msgFromO, destSocket)
            elif msg.split()[0] == "HISTORY_REQ":
                destClientID = msg.split("(")[1][:-1] # The ID of the chat you want to see a history of
                sessionID = getSessionID(clientID,destClientID) # Session ID of the chat
                # define a keyword
                keyword = str(sessionID)
                with open('data.json') as json_file:
                    #read json file line by line
                    for line in json_file.readlines():
                        # create python dict from json object
                        json_dict = json.loads(line)
                        # check if line contains keyword if so send back to client
                        if any(keyword in json_dict):
                            historyData = json_dict
                            #sent a history response each time sessionID is found in history data
                            server.send("HISTORY_RESP ({0},{1})".format(clientID,historyData))
            else:
                print('This is the chat_started thread')


#THIS FUNCTION FORWARDS DESTINATION CLIENT MESSAGES TO ORIGINATOR CLIENT MESSAGES
def OtoSmsgfowarding(server, clientID,destID):
    clientSocket = server.onlineSockets[clientID]
    destSocket = server.onlineSockets[destID]
    while True:
        #KEEP LISTENING FOR MESSAGES
        msgFromD = server.receive(destSocket)
        sessionID = getSessionID(clientID,destID) # Session ID of the chat
        data = sessionID + " from:" + destID + " " + msgFromD + "\n"
        #write to JSON history messages
        with open('data.json', 'w',newline='') as outfile:
            json.dump(data, outfile)

        if "CHAT" in msgFromD:
            msgFromD = msgFromD.split(',')[1][:-1]
        elif "END_REQUEST" in msgFromD:
            print("b sent end notif")
            server.onlineSessions[getSessionID(clientID, destID)] = None
            server.send("END_NOTIF ({0})".format(getSessionID(clientID, destID)), clientSocket)
            server.send("END_NOTIF ({0})".format(getSessionID(clientID, destID)), destSocket)
            break
        
        #PRINT MESSAGES TO SERVER
        print(msgFromD)

        #FORWARD MESSAGE TO ORIGINATOR
        if msgFromD != "":
            server.send(msgFromD, clientSocket)

        elif msg.split()[0] == "HISTORY_REQ":
                destClientID = msg.split("(")[1][:-1] # The ID of the chat you want to see a history of
                sessionID = getSessionID(clientID,ID) # Session ID of the chat
                keyword = str(sessionID)

                with open('data.json') as json_file:
                    #read json file line by line
                    for line in json_file.readlines():
                        # create python dict from json object
                        json_dict = json.loads(line)
                        # check if line contains keyword if so send back to client
                        if any(keyword in json_dict):
                            historyData = json_dict
                            #sent a history response each time sessionID is found in history data
                            server.send("HISTORY_RESP ({0},{1})".format(destID,historyData))

def main():
    server = ChatServer()
    print ('SERVER HAS STARTED')
    while True:
        clientInfo = server.acceptConnection()
        thread = threading.Thread(target=connectClient, args=(server,clientInfo))
        thread.start()
            
#allow client to log in
if __name__ == "__main__":
    main()
        
        
