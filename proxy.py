'''
Created on 11/16/2014

@author: mayank juneja
'''

'''
Importing required libraries
'''
import os,sys,thread,socket
import time
import datetime
from os import curdir, sep, linesep

class Proxy(object):
    maxData = 999999
    cache = {}
    timeout = 2
    logf = open('proxyLog.txt', 'w+')

    '''
    Functions to return various Time Stamps
    '''
    def timestamp(self):
        return time.strftime("%a, %d %b %Y %X GMT", time.gmtime())
    def timestamp2(self):
        return time.strftime("%d %b %Y %X GMT", time.gmtime())
    def timedate(self):
        return time.strftime("%d", time.gmtime())
    def timemonth(self):
        return time.strftime("%b", time.gmtime())
    def timeyear(self):
        return time.strftime("%Y", time.gmtime())
    def timetime(self):
        return time.strftime("%X", time.gmtime())

    '''
    Function to Lof to a file stored in home directory
    '''
    def logIt(self, ip, port, url, r):
        logf.write(str(ip)+" "+str(port)+" "+str(url)+" "+str(timestamp())+" "+r+"\n")

    '''
    Function to write Block or hold operations on console
    '''
    def printCon(self, type, request, address):
        print address[0],"\t",type,"\t",request

    '''
    Function to retrieve data from cache
    '''
    def getCache(self, client, key):
        d2 = ''
        d2 = self.cache.get(key)
        if(d2>0):
            d3 = d2.split('||||')[0]
            time = d3.split(' ')
            if (timedate() == time[0]):							#Checking if date is same
                if(timemonth() == time[1]):						#Checking if month is same
                    if(timeyear() == time[2]):					#Checking if year is same
                        if(timetime().split(':')[0] == time[3].split(':')[0]):	#Checking if hours are same
                            minutes = time[3].split(':')[1]
                            if(int(timetime().split(':')[1])- int(minutes) < 3): #Checking if the difference between two times is less than 3
                                client.send(d2.split('||||')[1])
                                client.close()
                                return True
        else:
            return False

    '''
    Function to delete the expired cache
    '''
    def refreshCache(self):
        for k, v in self.cache.items():
            d4 = v.split('||||')[0]
            d5 = d4.split(' ')[3]
            if(int(d5.split(':')[1]) - int(timetime().split(':')[1]) > 2):
                del self.cache[k]
		
    '''
    Funtion to memorize cached data
    '''
    def memorize(self, key, data):
        if('200 OK' in data):		#Checking if data is valid
            d = timestamp2()+'||||'+data
            self.cache[key] = d


    '''
    Function to start a thread
    '''
    def start(self, client, client_addr):
        dataSent=''
        i=0
        data = client.recv(self.maxData)
        forUrl=''
        url = ''
        if (len(data)>1):						#Checking if request is received
            forUrl = data.split('\n')[0]
            url = forUrl.split(' ')[1]				#Extracting client's request
            if '.jpg' in url:					#Block if request is jpg
            	self.printCon("Blocked",forUrl,client_addr)
                response='HTTP/1.1 501 Not Implemented:\r\n'
                response+="Connection: keep-alive\r\n"
                response+='Content-Type: text/html\r\n\r\n'
                response+='<HTML><HEAD><TITLE>Server does not support this filetype\r\n'
                response+='</TITLE></HEAD>\r\n'
            	response+='<BODY><P>BLOCKED BY PROXY:: Server can not open .jpg'
            	response+='\r\n</BODY></HTML>\r\n'
            	client.send(response)				#Send Block instructions
            	client.close()
            	sys.exit(1)

            else:
                response='HTTP/1.1 500 Internal Server Error:\r\n'
                response+="Connection: keep-alive\r\n"
                response+="Date:"+timestamp()+"\r\n"
                response+='Content-Type: text/html\r\n\r\n'
                response+='<HTML><HEAD><TITLE>Server has unexpected error\r\n'
                response+='</TITLE></HEAD>\r\n'
                response+='<BODY><P>Improper Data Request'
                response+='\r\n</BODY></HTML>\r\n'
                client.send(response)
        position = url.find("://")
        if (position==-1): 						#when :// is not found
            var = url
        else: 							#Get url
            var = url[(position+3):]
        portPosition = var.find(":")
        webserverPosition = var.find("/")
        if webserverPosition == -1:					#when / is not found
            webserverPosition = len(var)
        webserver = ""
        port = -1
        if (portPosition==-1 or webserverPosition < portPosition):  # default port
            port = 80
            webserver = var[:webserverPosition] 			#get webserver's name
            #print "default port: ",port
        else:       						# extract port number
            port = int((var[(portPosition+1):])[:webserverPosition-portPosition-1])
            webserver = var[:portPosition]
            #print "specific port: ",port
        #print "webserver: ",webserver
        self.refreshCache()
        getcache = self.getCache(client, forUrl)				#Checking and retreiving information from cache
        if(getcache == True):
            req = 'Cached'
            webserverIp=socket.gethostbyname(webserver)		#Getting Ip by name
            self.logIt(webserverIp, port, webserver, req)
            print "Cache Present"
        else:
            try:
                req = 'Not Cached'				#Creating socket to send data to the server
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                webserverIp=socket.gethostbyname(webserver)
                self.logIt(webserverIp, port, webserver, req)
                s.connect((webserverIp, port))
                s.send(data)					#Data sent to server
                chunk = 1
                response = ''
                while 1:
                    data = s.recv(maxData)			#Receiving server's response
                    if (len(data) > 0):
                        response+=data
                        client.send(data)
                        self.memorize(forUrl, response)	#Set data in Cache
                    else:
                        break
                #client.send(response)
                s.close()
                #memorize(forUrl,response)
                client.close()
            except socket.error, (value, message):
                if s:
                    s.close()
                    if client:
                        client.close()
                    self.printCon("Peer Reset",forUrl,client_addr)
                    sys.exit(1)

    '''
    Main function
    '''
    def main(self):
        if (len(sys.argv)<2):
            print "Please Enter in format [Filename] [Port Number]"
            sys.exit(1)
        else:
            port = int(sys.argv[1])
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', port))
            s.listen(50)
    
        except socket.error, (value, message):
            if s:
                s.close()
                print "Unable to create socket: ", message
                sys.exit(1)
        while 1:
            client, client_addr = s.accept()
            thread.start_new_thread(self.start, (client, client_addr))
        s.close()
    
if __name__ == '__main__':
    logf = open('proxyLog.txt', 'w+')
    logf.write("<ClientIPaddress> <ClientPortnumber> <Filerequested> <Timestamp>\n")
    proxy = Proxy()
    try:
        proxy.main()
    except KeyboardInterrupt:
        logf.close()
        print "Ctrl C - Stopping server"
        sys.exit(1)
