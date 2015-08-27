import socket
import re
import unittest

class LoginError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)



class FTPStruct:
	"""The tree sturcture that is used to store the folder branches"""
	def __init__(self, s):
		self.path = None
		self.s = s

	"""Checks to see if the name of the object has a file extension"""
	def isFile(self, name):
		"""
		>>> s = FTP("matthew", "ruckbau.com", "watchBuddies", "21")
		>>> ftp = FTPStruct(s)
		>>> ftp.isFile("Hello.py")
		True
		>>> ftp.isFile("folder")
		False
		"""
		match =  re.search('([.])\w+', name)
		if match:
			return True
		return False 

	def checkName(self, searchName, name):
		name = name.rstrip()
		return searchName == name

	def search(self, searchName, files, localPath):
		files = files[2:]
		folders = []
		for name in files:
			name = name.rstrip()
			if self.isFile(name):
				if self.checkName(searchName, name):
					self.path = localPath + "/" + name
					return self.path
			else:
				folders += [name]

		for folder in folders:
			print(folder)
			self.s.changeDIR(folder)
			files_n = self.s.listFiles()
			self.search(searchName, files_n, localPath + "/" + folder)
			if self.path == None:
				self.s.send("CDUP")
			else :
				return self.path

host = ''
port = None 
class FTP:
	"""Create a new FTP object with a host and password. Checks to see if the host can connect
	if not will exit and prompt again"""
	def __init__(self, user, host, password, port):
		self.user = user
		self.host = host
		self.password = password
		self.port = port
		self.error = 0
		self.shost = None
		self.sport = None
		self.passive = False
		if port == "":
			self.port = 21
		else:
			self.port = int(port)
		self.timeout = socket.getdefaulttimeout()
		self.error = False
		self.socket = None
		self.listenSocket = None
		connected = self.connect(self.host)
		if (connected):
			raise LoginError("Could not connect")
		# else:
		# 	print("successfully logged into: " + self.host + "@" + self.user)
		self.getresp()
		self.login()

	def login(self):
		send_user = "USER " + self.user + "\n"
		send_pass = "PASS " + self.password + "\n"
		self.socket.sendall(send_user.encode('latin-1'))
		resp1 = self.getresp()
		self.socket.sendall(send_pass.encode('latin-1'))
		resp2 = self.getresp()
		return self.error

	"Load a socket for sending and for recieving"
	def connect(self, host=None):
		# s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try :
			sock = socket.socket()
			sock.connect((self.host, self.port))
			self.socket = sock
			self.file = self.socket.makefile('r', encoding='latin-1')
			self.fam = self.socket.family
		except (ValueError, ConnectionRefusedError, TimeoutError):
			self.error = True
			self.socket = None
			self.fam = None
		return self.error

	def getline(self, files):
		line = files.readline(8192 + 1)
		return line

	# Internal: get a response from the server, which may possibly
	# consist of multiple lines.  Return a single string with no
	# trailing CRLF.  If the response consists of multiple lines,
	# these are separated by '\n' characters in the string
	def getmultiline(self, files):
		line = self.getline(files)
		if line[3:4] == '-':
			code = line[:3]
			while 1:
				nextline = self.getline(files)
				line = line + ('\n' + nextline)
				if nextline[:3] == code and \
						nextline[3:4] != '-':
					break
		return line

	"""	Internal: get a response from the server.
		Raise various errors if the response indicates an error"""
	def getresp(self, files=None):
		if files == None:
			files = self.file
		resp = self.getmultiline(files)
		return resp

	"""Lists the current working directory."""
	def workingDir(self):
		resp = self.send("PWD")
		if self.error:
			raise LoginError('Could not send command')
		return resp

	def getFile(self, fileName):
		files = []
		host, port = self.makepasv()
		sock = socket.socket()
		sock.connect((host, port))
		cmd = "RETR " + fileName
		resp = self.send(cmd)
		fp = sock.makefile('rb')
		line = fp.readline(8192 + 1)
		while line:
			if len(line) > 8192:
				raise Error("got more than %d bytes" % 8192)
			if line[-2:] == '\r\n':
				line = line[:-2]
			elif line[-1:] == '\n':
				line = line[:-1]
			line = line.decode("latin-1") 
			line = line.replace("\r", "")
			files += [line]
			line = fp.readline(8192 + 1)
		# print(files)
		sock.close()
		return files

	"""Lists files in the current directory"""
	def listFiles(self):
		host, port = self.makepasv()
		sock = socket.socket()
		sock.connect((host, port))
		files = self.getLSTResp(sock)
		if self.error:
			raise LoginError('Could not send command')
		sock.close()
		return files
		

	def getLSTResp(self, sock):
		resp = self.send('NLST')
		files = []
		fp = sock.makefile('rb')
		line = fp.readline(8192 + 1)
		while line:
			if len(line) > 8192:
				raise Error("got more than %d bytes" % 8192)
			if line[-2:] == '\r\n':
				line = line[:-2]
				line += "\n"
			# elif line[-1:] == '\n':
			# 	line = line[:-1]
			line = line.decode("latin-1") 
			line = line.replace("\r", "")
			files += [line]
			line = fp.readline(8192 + 1)
		self.getresp()
		fp.close()
		return files

	def makepasv(self):
		resp = self.send('PASV')
		host, port = self.parsePasv(resp)
		self.passive = True
		return host, port


	def parsePasv(self, resp):
		if resp[:3] != '227':
			raise LoginError("Error in pasv command")
		_227_re = re.compile(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)')
		m = _227_re.search(resp)
		if not m:
			raise LoginError("Error in PASV command")
		numbers = m.groups()
		host = '.'.join(numbers[:4])
		port = (int(numbers[4]) << 8) + int(numbers[5])
		return host, port


	"""Used to send all commands. Error checking is done outside of this function"""
	def send(self, cmd):
		cmd = cmd + '\n'
		sent = self.socket.sendall(cmd.encode('latin-1'))
		if sent is not None:
			self.error = True
		resp = self.getresp()
		return resp

	def sendport(self, host, port):
		'''Send a PORT command with the current host and the given
		port number.
		'''
		hbytes = host.split('.')
		pbytes = [repr(port//256), repr(port%256)]
		bytes = hbytes + pbytes
		cmd = 'PORT ' + ','.join(bytes)
		return self.send(cmd)


	def changeDIR(self, dirname):
		'''Change to a directory.'''
		if dirname == '..':
			resp = self.send('CDUP')
			return resp
		if dirname == '':
			dirname = '.'
		cmd = 'CWD ' + dirname
		resp = self.send(cmd)
		if self.error:
			raise LoginError("File name does not exist")
		return resp

	def close(self):
		self.socket.close()

	def recv(self, value):
		self.socket.recv(value)

def main():
	user = input("Username: ")
	host = input("Host: ")
	password = input("Password: ")
	try:

		s = FTP(user, host, password, "21")
		files = s.listFiles()
		ftp = FTPStruct(s)
		path = ftp.search("ants.py", files, "cs61as")
		# print(path)
		# s.getFile("hw.py")
		s.close()
	except LoginError as m:
		print(m)
	
	# s.close()

def doctesting():
	import doctest
	doctest.testmod()

class FTPUnitTest(unittest.TestCase):

	def test_isFile(self):
		s = FTP("matthew", "ruckbau.com", "watchBuddies", "21")
		ftp = FTPStruct(s)
		self.assertEqual(ftp.isFile("sample.py"), True)
		self.assertEqual(ftp.isFile("folder"), False)
		s.close()

	def test_ListFiles(self):
		s = FTP("matthew", "ruckbau.com", "watchBuddies", "21")
		s.changeDIR("cs61as")
		files = s.listFiles()
		files = s.listFiles()
		self.assertEqual(len(files), 6)
		self.assertEqual(s.error, 0)
		s.close()
	def test_pasv(self):
		s = FTP("matthew", "ruckbau.com", "watchBuddies", "21")
		packet = s.makepasv()
		self.assertEqual(s.passive, True)
		self.assertEqual(len(packet), 2) 
		s.close()
	def test_ChangeDIR(self):
		s = FTP("matthew", "ruckbau.com", "watchBuddies", "21")
		resp = s.changeDIR("cs61as")
		self.assertEqual(resp[:3], "250")
		s.close()
	def test_WorkingDir(self):
		s = FTP("matthew", "ruckbau.com", "watchBuddies", "21")
		s.changeDIR("cs61as")
		s.changeDIR("hw")
		resp = s.workingDir()
		self.assertEqual(resp[:3], "257")
		self.assertEqual(resp[5:15], "/cs61as/hw")
		s.close()


if __name__ == '__main__':
	unittest.main()

		

	
