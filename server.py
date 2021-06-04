import socket
import select
import sys
import threading
import re
from history import Record
import time
from authenticate import *
from random import *

ClientIDandIP = Record()
ClientIDandKey = Record()
clientID = 0
destClientID = 0
senderClientID = 0

def GETSESSIONID(id1,id2):
    if int(id1) < int(id2):
        return str(id1) + '-' + str(id2)

    return str(id2) + '-' + str(id1)

def sendChallenge(clientSocket):
    # GENERATE SECRET KEY AND ASSOCIATE IT WITH CLIENT ID
    seed(101)
    k_a = str((randint(0, 1000000) % 1000) + 1)  # CLIENT MUST ALSO HAVE THIS KEY FOR AUTHENTICATION
    print("Key is: " + k_a)#DEL THIS IF I FORGET
    ClientIDandKey.addMessage(clientID, k_a)
    # RAND VALUE TO BE USED IN AUTHENTICATION, VALUE MUST ALSO BE SENT TO CLIENT
    # THAT IS BEING CHALLENGED TO AUTHENTICATE
    seed(67)
    randNum = (randint(0, 1000000) % 5000) + 1
    xres = authenticate(randNum, k_a)
    print("Sending CHALLENGE")
    server.send("CHALLENGE {0} {1}".format(randNum, k_a), clientSocket)
    return xres, k_a, randNum

def CONNECTCLIENT(server, clientInfo):
    
    #GET CLIENT SOCKET
    clientSocket = clientInfo[0]
    #GET CLIENT ADDRESS AND PORT NUMBER
    client_address_port = clientInfo[1]
    #GET CLIENT IP ADDRESS
    client_address = str(client_address_port[0])
    # SEND CHALLENGE WITH RANDOMLY GENERATED NUMBER
    XRES, k_a, randNum= sendChallenge(clientSocket)
    # RECIEVE RES VALUES TO COMPARE WITH XRES VALUE TO AUTHENTICATE
    resMessage = server.receive(clientSocket)
    resMessage = resMessage.split()
    RES = resMessage[1]
    if RES == XRES:
        # TODO
        print("Authentication is successful")
        CK_A = generateKey(randNum, k_a)
        print("Cipher key generated")
        # REQUIREMENT IS TO SEND ALL DATA ENCRYPTED WITH KEY, BUT LEFT AS IS
        server.send("AUTH_SUCCESS", clientSocket)
        time.sleep(5)
        # SEND CONNECTED MESSAGE TO CLIENT
        server.send('CONNECTED', clientSocket)

    else:
        # TODO
        print("Authentication has failed")
        server.send('AUTH_FAIL', clientSocket)

    #SEND CONNECTED MESSAGE TO CLIENT
    server.send('CONNECTED',clientSocket)
    #GET CLIENT ID FROM CLIENT
    clientID = server.receive(clientSocket)[6]
    #ADD CLIENT ID AND IP ADDRESS TO DICTIONARY
    ClientIDandIP.addMessage(clientID, client_address)
    
    #PRINT NEW CLIENT LIST WHEN CLIENT IS ADDED
    print('CLIENT ' + clientID + ' has joined the chat!')
    print('***********\nClient List\n-----------')
    ClientIDandIP.print()
    print('***********')
    #ADD ONLINE SOCKET TO LIST
    server.clientSocks[clientID] = clientSocket
    #ADD CLIENT ID TO LIST
    server.listOfClientIDs.append(clientID)

    #HOLDS DESTINATION CLIENT ID SO THAT IT IS SHARED BETWEEN CLIENTS
    global destClientID
    inChatMode = False
    
    #GET CLIENT COMMAND
    client_command = server.receive(clientSocket)
    
    #IF STATEMENT FOR CLIENT MAKING CHAT REQUEST
    if re.match(r'CHAT-REQUEST [0-9]+ from [0-9]+', client_command):
        #GET 
        destClientID = client_command[13]
        global senderClientID
        senderClientID = client_command[20]
        time.sleep(10)
        #print(senderClientID + ' to ' + destClientID)
        destClientResponse = server.receive(clientSocket)
        if destClientResponse == 'CHAT_STARTED RECV':
            inChatMode = True
    #IF USER CHOOSES TO WAIT
    elif client_command == 'WAITING':
        print(clientID + ' is listening')
        time.sleep(10)
        print (clientID + ' stopped listening')
        #IF THE USER IS BEING CHAT REQUESTED
        if clientID == destClientID:
            #TELL THE CLIENT
            server.send('CHAT-REQUESTED from ' + senderClientID , clientSocket)
            #GET CLIENT RESPONSE
            clientResponse = server.receive(clientSocket)
            #IF USER CHOOSES TO ACCEPT CHAT REQUEST 
            if clientResponse == 'ACCEPTED':
                #TELL THE CHAT REQUEST SENDER CLIENT THAT THEIR RQUEST HAS BEEN APPROVED
                server.send('CHAT_STARTED', server.clientSocks[senderClientID])
                inChatMode = True
            elif clientResponse == 'DENIED':
                #TELL THE CHAT REQUEST SENDER CLIENT THAT THEIR RQUEST HAS BEEN DENIED
                server.send('DENIED', server.clientSocks[senderClientID])
    #IF USERS BEGIN A CHAT SESSION
    if inChatMode == True:
        #SLEEP SO THAT USERS CAN SYNC
        time.sleep(5)
        destSocket = server.clientSocks[destClientID]
        server.chatSessions[GETSESSIONID(clientID, destClientID)] = 'ONLINE'

        #IF YOU ARE THE ORIGINATOR 
        if clientID != destClientID:
            print('Client ' + clientID + ' initiated chat with client ' + destClientID)
            OtoSmsgThread = threading.Thread(target=OtoSmsgfowarding, args=(server, clientID, destClientID))
            OtoSmsgThread.start()
            
        #BEGIN LISTENING FOR MESSAGES FROM THE ORIGINATOR TO THE DESTINATION
        while True:
            #KEEP LISTENING FOR MESSAGES
            msgFromO = server.receive(clientSocket)
            
            if 'CHAT' in msgFromO:
                msgFromO = msgFromO.split(',')[1][:-1] # CHAT (sessionID,This is the message)
            elif 'END_REQUEST' in msgFromO:
                print('a sent end notif')
                server.chatSessions[GETSESSIONID(clientID, destClientID)] = 'OFFLINE'
                server.send('END_NOTIF ({0})'.format(GETSESSIONID(clientID, destClientID)), clientSocket)
                server.send('END_NOTIF ({0})'.format(GETSESSIONID(clientID, destClientID)), destSocket)
                break
            
            #PRINT MESSAGE TO SERVER
            print(clientID + ': ' + msgFromO)
            
            #FORWARD MESSAGE TO DESTINATION
            if msgFromO != '':
                server.send(msgFromO, destSocket)
            elif msg.split()[0] == 'HISTORY_REQ':
                destClientID = msg.split('(')[1][:-1] # The ID of the chat you want to see a history of
                sessionID = GETSESSIONID(clientID,destClientID) # Session ID of the chat
            else:
                print('This is the chat_started thread')


#THIS FUNCTION FORWARDS DESTINATION CLIENT MESSAGES TO ORIGINATOR CLIENT MESSAGES
def OtoSmsgfowarding(server, clientID,destID):
    clientSocket = server.clientSocks[clientID]
    destSocket = server.clientSocks[destID]
    while True:
        #KEEP LISTENING FOR MESSAGES
        msgFromD = server.receive(destSocket)

        if 'CHAT' in msgFromD:
            msgFromD = msgFromD.split(',')[1][:-1]
        elif 'END_REQUEST' in msgFromD:
            print('b sent end notif')
            server.chatSessions[GETSESSIONID(clientID, destID)] = 'OFFLINE'
            server.send('END_NOTIF ({0})'.format(GETSESSIONID(clientID, destID)), clientSocket)
            server.send('END_NOTIF ({0})'.format(GETSESSIONID(clientID, destID)), destSocket)
            break
        
        #PRINT MESSAGES TO SERVER
        print(destID + ': ' + msgFromD)

        #FORWARD MESSAGE TO ORIGINATOR
        if msgFromD != '':
            server.send(msgFromD, clientSocket)


            
#CLASS FOR GENERAL SERVER CHAT FUNCTIONS
class CHATSERVER:
    def __init__(self):
        print ('INITIALIZING SERVER CLASS')
        self.portNumber = 8888
        self.listOfClientIDs = []
        self.clientSocks = {'1':None, '2':None, '3':None, '4':None, '5':None,
                              '6':None, '7':None, '8':None, '9':None, '10':None}
        self.chatSessions = {'-421341234' :'OFFLINE'}
        self.serverListenSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverListenSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverListenSock.bind((socket.gethostname(), self.portNumber))
        self.serverListenSock.listen(5)

    def send(self,data,clientSocket):
        clientSocket.send(data.encode())
    def receive(self, clientSocket):  
        return clientSocket.recv(2048).decode()

    def acceptConnection(self):
        clientInfo = self.serverListenSock.accept()
        return clientInfo
    
def main():
    global server
    server = CHATSERVER()
    print ('SERVER HAS STARTED')
    while True:
        clientInfo = server.acceptConnection()
        thread = threading.Thread(target=CONNECTCLIENT, args=(server,clientInfo))
        thread.start()
            
#allow client to log in
if __name__ == '__main__':
    main()
        
        
