#  monitor.py (c) 2019 Michel Anders
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA. 

# TODO
# x readline support (command completion, history, ...)
# x break up large chunks when sending (if needed)
# x binary file loading
# - echo matching (to verify is a command is understood//echoed)
# x run <address>
# x add flush read buffer before each command exec (except flush)
# x help command
# - error checking
# x sanitize code, split op in proper reusable functions
# - nice to have: TEST <addr> <byte> ...
# - nice to have: serial line name and properties configurable via argparse
#
# Note: this is not a proper terminal program as both sending and
# receiving is done in the same thread. This makes recovering from
# a hung connection impossible but it consider it good enough :-)

import serial
from time import sleep
import cmd


class Monitor(cmd.Cmd):
	def preloop(self):
		self.ser = serial.Serial(port='/dev/ttyUSB1', stopbits=serial.STOPBITS_TWO)
		self.lastaddr = 0

	def postloop(self):
		self.ser.close()

	def flush(self, nbytes=0):
		"""
		read a number of bytes.
		
		for nbytes > 0 will wait for that exact number of bytes
		for nbytes = 0 will keep readin bytes as long as they are coming
		"""
		if nbytes:
			while not self.ser.in_waiting:
				sleep(0.1)
			ret = self.ser.read(nbytes)
		else:
			while self.ser.in_waiting:
				ret = self.ser.read(self.ser.in_waiting)
				sleep(0.1)

	def splitdump(self, line):
		"""
		split line into arguments:  ADDR [LEN]
		"""
		self.args = line.strip().split()
		self.addr = int(self.args[0],16) if len(self.args) > 0 else self.lastaddr
		self.length = int(self.args[1], base=0) if len(self.args) > 1 else 0
		self.hexbytes = []
		self.lastaddr = self.addr 
		return self.addr

	def splitload(self, line):
		"""
		split line into arguments:  ADDR BYTE [BYTE ...] or ADDR "string"
		"""
		self.args = line.strip().split()
		self.addr = int(self.args[0],16)
		q = line.find('"')
		hexbytes = []
		if q >= 0:
			for c in line[q+1:]:
				if c == '"': break
				hexbytes.append(ord(c))
			hexbytes.append(0)
			self.length = len(hexbytes)
		else:
			if len(self.args) > 1:
				hexbytes = [int(hb,base=0) for hb in self.args[1:]]
				self.length = len(hexbytes)
			else:
				self.length = 0
		self.hexbytes = hexbytes
		return self.addr

	def wait(self,t):
		"""
		wait for bytes to become available on the receive line.
		
		waits t seconds between tries.
		"""
		while not self.ser.in_waiting:
			sleep(t)

	def do_dump(self, line):
		"""
		dump <hexaddr> <length>          dump bytes
		"""
		self.flush()
		addr = self.splitdump(line)
		if self.length == 0:
			self.length = 48
		data = [(addr >> 8), (addr & 255), (128+self.length)]
		self.ser.write(bytes(data))
		self.wait(0.1)
		self.flush(len(data))
		self.wait(0.1)
		count = 0
		needaddr = True
		while self.ser.in_waiting:
			ret = self.ser.read(self.ser.in_waiting)
			for b in ret:
				if needaddr:
					print("%04x "%addr, end='')
					needaddr = False
				print("%02x "%int(b), end='')
				count += 1
				if count % 8 == 0:
					addr += 8
					print("")
					needaddr = True
			sleep(0.1)
		print('\nok')
		return False

	def do_dumps(self, line):
		"""
		dumps <hexaddr> [<length>]          dump string (max <length> bytes or 48 bytes if omitted)
		"""
		self.flush()
		addr = self.splitdump(line)
		if self.length == 0:
			self.length = 48
		data = [(addr >> 8), (addr & 255), (128+self.length)]
		self.ser.write(bytes(data))
		self.wait(0.1)
		self.flush(len(data))
		self.wait(0.1)
		count = 0
		print("%04x "%addr, end='')
		while self.ser.in_waiting:
			ret = self.ser.read(self.ser.in_waiting)
			print(ret.decode('utf-8', "backslashreplace"), end='')
			sleep(0.1)
		print('\nok')
		return False

	def do_load(self, line):
		"""
		load <hexaddr> <length> <hexbyte> ...  load <length> bytes into memory
		"""
		self.flush()
		addr = self.splitload(line)
		if self.length:
			data = [(addr >> 8), (addr & 255), (64+self.length)]
			self.ser.write(bytes(data))
			self.wait(0.1)
			self.flush(len(data))
			self.ser.write(bytes(self.hexbytes))
			self.wait(0.1)
			self.flush(len(self.hexbytes))
			print('ok')
		else:
			print("no bytes specified")
		return False

	def do_file(self, line):
		"""
		file <filename>    load binary contents of <filename> into mem at $0000
		"""
		self.flush()
		args = line.strip().split()
		try:
			with open(args[0], 'rb') as f:
				hexbytes = f.read()
				length = len(hexbytes)
		except FileNotFoundError:
			print("file not found")
			return False
		addr = 0
		while length > 63:
			data = [(addr >> 8), (addr & 255), (64+63)]
			self.ser.write(bytes(data))
			self.wait(0.1)
			self.flush(len(data))
			send = hexbytes[addr:addr+63]
			self.ser.write(send)
			self.wait(0.1)
			self.flush(len(send))
			addr += 63
			length -= 63
		if length > 0:
			data = [(addr >> 8), (addr & 255), (64+length)]
			self.ser.write(bytes(data))
			self.wait(0.1)
			self.flush(len(data))
			send = hexbytes[addr:addr+length]
			self.ser.write(send)
			self.wait(0.1)
			self.flush(len(send))
		print('ok')
		return False

	def do_run(self, line):
		"""
		run <hexaddress> 	run program at <hexaddress> showing output as hexbytes
		"""
		self.flush()
		addr = self.splitload(line) # only interested in address, bytes will be ignored
		data = [(addr >> 8), (addr & 255), (0xc0)]
		self.ser.write(bytes(data))
		self.wait(0.1)
		self.flush(len(data))
		print('running...')
		count = 0
		again = True
		while again:
			again = False
			while self.ser.in_waiting:
				ret = self.ser.read(self.ser.in_waiting)
				for b in ret:
					print("%02x "%int(b), end='')
					count += 1
					if count % 16 == 0:
						print('')
				sleep(0.1)
			sleep(1.0) # timeout, we do not know when a program is going to end
			again = self.ser.in_waiting > 0
		print('\nok')
		return False

	def do_runs(self, line):
		"""
		runs <hexaddress> 	run program at <hexaddress> showing output as unicode chars
		"""
		self.flush()
		addr = self.splitload(line)
		data = [(addr >> 8), (addr & 255), (0xc0)]
		self.ser.write(bytes(data))
		self.wait(0.1)
		self.flush(len(data))
		print('running...')
		count = 0
		again = True
		while again:
			again = False
			while self.ser.in_waiting:
				ret = self.ser.read(self.ser.in_waiting)
				print(ret.decode('utf-8', "backslashreplace"), end='')
				sleep(0.1)
			sleep(1.0) # timeout, we do not know when a program is going to end
			again = self.ser.in_waiting > 0
		print('\nok')
		return False

	def do_flush(self, line):
		"""
		flush		dump any remaining characters in receive buffer.
		"""
		count = 0
		while self.ser.in_waiting:
			ret = self.ser.read(ser.in_waiting)
			for b in ret:
				print("%02x "%int(b), end='')
				count += 1
				if count % 16 == 0:
					print('')
			sleep(0.1)
			print('\nok')
		return False

	def do_exit(self, line):
		"""
		exit		exit monitor program
		"""
		self.flush()
		return True

if __name__ == '__main__':
    m = Monitor()
    m.prompt = '>'
    m.cmdloop()
