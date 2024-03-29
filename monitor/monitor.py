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
# x some error checking
# x sanitize code, split op in proper reusable functions
# x nice to have: TEST <addr> <byte> ...
# - nice to have: serial line name and properties configurable via argparse
#
# Note: this is not a proper terminal program as both sending and
# receiving is done in the same thread. This makes recovering from
# a hung connection impossible but it consider it good enough :-)

import serial
from time import sleep, time
import cmd
from glob import glob
import os.path
from threading import Thread

try:
	import readline
except ImportError:
	readline = None

histfile = os.path.expanduser('~/.monitor_history')
histfile_size = 1000


# https://stackoverflow.com/questions/16826172/filename-tab-completion-in-cmd-cmd-of-python
def _complete_path(path):
	if os.path.isdir(path):
		return glob(os.path.join(path, '*'))
	else:
		return glob(path+'*')

class Monitor(cmd.Cmd):
	def __init__(self):
		super().__init__()
		self.scriptmode = False

	def complete_file(self, text, line, start_idx, end_idx):
		return _complete_path(text)

	def preloop(self):
		if readline:
			readline.set_completer_delims(' \t\n')
		if readline and os.path.exists(histfile):
			readline.read_history_file(histfile)
		self.ser = serial.Serial(port=self.dev, stopbits=serial.STOPBITS_TWO)
		self.lastaddr = 0

	def postloop(self):
		self.ser.close()
		if readline:
			readline.set_history_length(histfile_size)
			readline.write_history_file(histfile)

	def precmd(self, line):
		if self.scriptmode: print(line)
		if line.strip().startswith("#") : return ''
		return(line)

	def do_EOF(self, line):
		return True

	def emptyline(self):  # empty lines are ignored because it is dangerous to run a command implicitely
		pass

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
		self.options = {a[1:]:True for a in self.args if a.startswith("-")}
		self.args = [a for a in self.args if not a.startswith("-")]
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
		self.string = False
		if q >= 0:
			for c in line[q+1:]:
				if c == '"': break
				hexbytes.append(ord(c))
			hexbytes.append(0)
			self.length = len(hexbytes)
			self.string = True
		else:
			if len(self.args) > 1:
				hexbytes = [int(hb,base=0) for hb in self.args[1:]]
				self.length = len(hexbytes)
			else:
				self.length = 0
		self.hexbytes = hexbytes
		return self.addr

	def splitrun(self, line):
		"""
		split line into arguments:  ADDR [args ...]
		"""
		self.args = line.strip().split()
		self.addr = int(self.args[0],16)
		hexbytes = []
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
		if self.length == 0 or self.length > 63:
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
				if 'd' in self.options:
					if 's' in self.options:
						w = int(b)
						if w > 0x7f : w = -(0x100 - w)
						print("%4d "%w, end='')
					else:
						print("%3d "%int(b), end='')
				else:
					print("%02x "%int(b), end='')
				count += 1
				if count % 8 == 0:
					addr += 8
					print("")
					needaddr = True
			sleep(0.1)
		if not self.scriptmode: print('\nok')
		return False

	def do_dumpw(self, line):
		"""
		dumpw [-d] [-s] <hexaddr> <length>          dump words (big-endian)
		"""
		self.flush()
		addr = self.splitdump(line)
		if self.length & 1 : self.length -= 1  # make it even
		if self.length == 0 or self.length > 63:
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
			w = 0
			first = True
			for b in ret:
				if first:
					w = int(b) * 256
				first = not first
				if needaddr:
					print("%04x "%addr, end='')
					needaddr = False
				if first:
					if 'd' in self.options:
						if 's' in self.options:
							ww = w + int(b)
							if ww > 0x7fff: ww = -(0x10000 - ww)
							print("%6d "%(ww), end='')
						else:
							print("%5d "%(w + int(b)), end='')
					else:
						print("%04x "%(w + int(b)), end='')
				count += 1
				if count % 8 == 0:
					addr += 8
					print("")
					needaddr = True
			sleep(0.1)
		if not self.scriptmode: print('\nok')
		return False

	def do_dumpl(self, line):
		"""
		dumpl [-d] [-s] <hexaddr> <length>          dump long words (big-endian)
		"""
		self.flush()
		addr = self.splitdump(line)
		if self.length & 1 : self.length -= 1  # make it even
		if self.length == 0 or self.length > 63:
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
			w = 0
			nb = 0
			for b in ret:
				w *= 256
				w += int(b)
				nb += 1
				if needaddr:
					print("%04x "%addr, end='')
					needaddr = False
				if nb == 4:
					if 'd' in self.options:
						if 's' in self.options:
							if w > 0x7fffffff: w = -(0x100000000 - w)
							print("%10d "%(w), end='')
						else:
							print("%11d "%(w), end='')
					else:
						print("%08x "%(w), end='')
					nb = 0
					w = 0
				count += 1
				if count % 8 == 0:
					addr += 8
					print("")
					needaddr = True
			sleep(0.1)
		if not self.scriptmode: print('\nok')
		return False

	def do_dumps(self, line):
		"""
		dumps <hexaddr> [<length>]          dump string (max <length> bytes or 48 bytes if omitted)
		"""
		self.flush()
		addr = self.splitdump(line)
		if self.length == 0 or self.length > 63:
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
		if not self.scriptmode: print('\nok')
		return False

	def do_load(self, line):
		"""
		load <hexaddr> <byte> ...  load bytes into memory
		"""
		self.flush()
		addr = self.splitload(line)
		if self.length and self.length < 63:
			data = [(addr >> 8), (addr & 255), (64+self.length)]
			self.ser.write(bytes(data))
			self.wait(0.1)
			self.flush(len(data))
			self.ser.write(bytes(d if d>=0 else 256+d for d in self.hexbytes))
			self.wait(0.1)
			self.flush(len(self.hexbytes))
			if not self.scriptmode: print('ok')
		else:
			print("no bytes specified or more than 62")
		return False

	def do_loadw(self, line):
		"""
		loadw <hexaddr> <word> ...  load words into memory
		"""
		self.flush()
		addr = self.splitload(line)
		if self.length and self.length < 31:
			self.length *= 2
			data = [(addr >> 8), (addr & 255), (64+self.length)]
			self.ser.write(bytes(data))
			self.wait(0.1)
			self.flush(len(data))
			data = [d.to_bytes(2,byteorder='big',signed=(d < 0x8000)) for d in self.hexbytes]
			data = [item for sublist in data for item in sublist]
			self.ser.write(bytes(data))
			self.wait(0.1)
			self.flush(len(self.hexbytes))
			if not self.scriptmode: print('ok')
		else:
			print("no words specified or more than 30")
		return False

	def do_loadl(self, line):
		"""
		loadl <hexaddr> <long> ...  load long words into memory
		"""
		self.flush()
		addr = self.splitload(line)
		if self.length and self.length < 15:
			self.length *= 4
			data = [(addr >> 8), (addr & 255), (64+self.length)]
			self.ser.write(bytes(data))
			self.wait(0.1)
			self.flush(len(data))
			data = [d.to_bytes(4,byteorder='big',signed=(d < 0x80000000)) for d in self.hexbytes]
			data = [item for sublist in data for item in sublist]
			self.ser.write(bytes(data))
			self.wait(0.1)
			self.flush(len(self.hexbytes))
			if not self.scriptmode: print('ok')
		else:
			print("no words specified or more than 14")
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
		if not self.scriptmode: print('ok')
		return False

	def do_run(self, line):
		"""
		run <hexaddress> 	run program at <hexaddress> showing output as hexbytes
		"""
		self.flush()
		addr = self.splitrun(line)
		data = [(addr >> 8), (addr & 255), (0xc0)]
		self.ser.write(bytes(data))
		self.wait(0.1)
		self.flush(len(data))
		if not self.scriptmode: print('running...')
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
		if not self.scriptmode: print('\nok')
		return False

	def reads(self):
		while True:
			while self.ser.in_waiting:
				ret = self.ser.read(self.ser.in_waiting)
				dt = time() - self.starttime
				string = ret.decode('utf-8', "backslashreplace")
				if self.timestamp:
					lines = string.split('\n')
					t = "[%6.3f] \n"%dt
					string = t.join(lines)
				print(string, end='', flush=True)
				if self.stop:
					return
				sleep(0.1)
			if self.stop:
				return

	def read(self):
		count = 0
		while True:
			while self.ser.in_waiting:
				ret = self.ser.read(self.ser.in_waiting)
				for b in ret:
					print("%02x "%int(b), end='', flush=True)
					count += 1
					if count % 16 == 0:
						print('')
				if self.stop:
					return
				sleep(0.1)
			if self.stop:
				return


	def do_runp(self, line):
		"""
		runp <hexaddress> 	run program at <hexaddress> with a separate read process, showing output as hexbytes
		"""
		self.flush()
		addr = self.splitrun(line)
		data = [(addr >> 8), (addr & 255), (0xc0)]
		self.ser.write(bytes(data))
		self.wait(0.1)
		self.flush(len(data))
		if not self.scriptmode: print('running...')
		self.stop = False
		p = Thread(target = self.read)
		p.start()
		again = True
		while again:
			try:
				inp = input()
				inp += '\n'
				self.ser.write(bytes([ord(i) for i in inp]))
			except:
				again = False
				self.stop = True
		if not self.scriptmode: print('\nok')
		return False

	def do_runps(self, line):
		"""
		runps <hexaddress> 	run program at <hexaddress> with a separate read process, showing output as unicode strings
		"""
		self.flush()
		addr = self.splitrun(line)
		self.timestamp = False
		if len(self.args) > 1 and self.args[1] == '-t':
			self.timestamp = True
		data = [(addr >> 8), (addr & 255), (0xc0)]
		self.ser.write(bytes(data))
		self.wait(0.1)
		self.flush(len(data))
		if not self.scriptmode: print('running...')
		self.stop = False
		p = Thread(target = self.reads)
		p.start()
		again = True
		while again:
			try:
				self.starttime = time()
				inp = input()
				inp += '\n'
				self.ser.write(bytes([ord(i) for i in inp]))
			except:
				again = False
				self.stop = True
		if not self.scriptmode: print('\nok')
		return False

	def do_test(self, line):
		"""
		test <hexaddress> (<len> <byte> ... | "string" )   verify contents of memory 
		"""
		self.flush()
		addr = self.splitload(line)
		compare = bytearray(self.hexbytes)
		string = self.string
		if self.length == 0 or self.length > 63:
			print("no length specified, empty string or more than 63 bytes")
			return False
		data = [(addr >> 8), (addr & 255), (128+self.length)]
		self.ser.write(bytes(data))
		self.wait(0.1)
		self.flush(len(data))
		self.wait(0.1)
		result = bytearray()
		while self.ser.in_waiting:
			ret = self.ser.read(self.ser.in_waiting)
			result.extend(ret)
			sleep(0.1)
		if len(compare) != len(result):
			print("not ok (unequal lengths)")
		else:
			i = 0
			error = "ok"
			for original,returned in zip(compare,result):
				if original != returned:
					if string:
						error = "not ok (at pos %d, [%s|%s])" % (i,compare.decode('utf-8', "backslashreplace"), result.decode('utf-8', "backslashreplace"))
					else:
						error = "not ok (at pos %d, [%s|%s])" % (i," ".join(["%02x"%int(b) for b in compare]), " ".join(["%02x"%int(b) for b in result]))
					break
				i += 1
			if not self.scriptmode or error != 'ok': print(error) 
		return False

	def do_runs(self, line):
		"""
		runs <hexaddress> 	run program at <hexaddress> showing output as unicode chars
		"""
		self.flush()
		addr = self.splitrun(line)
		data = [(addr >> 8), (addr & 255), (0xc0)]
		self.ser.write(bytes(data))
		self.wait(0.1)
		self.flush(len(data))
		if not self.scriptmode: print('running...')
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
		if not self.scriptmode: print('\nok')
		return False

	def do_flush(self, line):
		"""
		flush		dump any remaining characters in receive buffer.
		"""
		count = 0
		while self.ser.in_waiting:
			ret = self.ser.read(self.ser.in_waiting)
			for b in ret:
				print("%02x "%int(b), end='')
				count += 1
				if count % 16 == 0:
					print('')
			sleep(0.1)
		if not self.scriptmode: print('\nok')
		return False

	def do_break(self, line):
		"""
		break		dump any remaining characters in receive buffer and send break.
		"""
		self.do_flush(line)
		self.ser.send_break()
		return False

	def do_exit(self, line):
		"""
		exit		exit monitor program
		"""
		self.flush()
		return True

if __name__ == '__main__':
	from argparse import ArgumentParser
	from serial.tools import list_ports

	parser = ArgumentParser()
	parser.add_argument('-t', '--test', help='run in test mode (will not show prompts)', action="store_true")
	parser.add_argument('-i', '--icestick', help='find icestick', action="store_true")
	parser.add_argument('dev', nargs='?', default='/dev/ttyUSB1', help='serial device to connect to (will default to /dev/ttyUSB1')

	args = parser.parse_args()

	m = Monitor()
	m.dev = args.dev
	if args.icestick:
		m.dev = sorted([p.device for p in list_ports.comports() if p.vid == 0x0403 and p.pid == 0x6010])[-1]
	m.prompt = '' if args.test else '>'
	m.scriptmode = args.test
	m.cmdloop()
