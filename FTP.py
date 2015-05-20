import socket 

host = ''
port = None 
class FTP(object):
	"""docstring for FTP"""
	def __init__(self, arg):
		super(FTP, self).__init__()
		self.acct = arg[0]
		self.pswd = arg[1]
		self.host = ''
		self.port = None
		self.timeout = socket.getdefaulttimeout()
		self.error = 0
		self.s = None
	"Load a socket for sending and ine for recieving"
	def loadInfo: 
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try :
			socket.create_connection(self.addr, self.timeout)
			break 
		except ValueError
			print "Could not connect"
		acct = 'ACCT' + user + pswd
		self.s = (acct)
	def getInfo(self):
		"From the socket get the directoy listings"
		smake = self.s.makefile()

	def currDir(self): 
		"Use pwd to display the wokring directory"
		resp = self.s.send('PWD')
		#check if resp is okay by looking at how many bytes were sent
	def changeDir(self, dirname):
		if dirname == ''
			dirname = '.'
		dirname = CWD + dirname
		resp = self.s.send(dirname)
		#check for resp 
	