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

import serial
from time import sleep

# TODO
# - readline support (command completion, history, ...)
# x break up large chunks when sending (if needed)
# x binary file loading
# - echo matching (to verify is a command is understood//echoed)
# x run <address>
# - add flush read buffer before each commad exec
# - help command
# - error checking
# - sanitize code, split op in proper reusable functions

with serial.Serial(port='/dev/ttyUSB1', stopbits=serial.STOPBITS_TWO) as ser:
	stopped = False
	while not stopped:
		line = input('>')
		cmd = line.split()
		cmd[0] = cmd[0].strip()
		if cmd[0] == 'exit':
			stopped = True
		elif cmd[0] in { 'dump', 'dumps' }:
			addr = int(cmd[1],16)
			length = int(cmd[2])
			data = [(addr >> 8), (addr & 255), (128+length)]
			send = bytes(data)
			ser.write(send)
			while not ser.in_waiting:
				sleep(0.1)
			# TODO match against input bytes first
			ret = ser.read(3)
			while not ser.in_waiting:
				sleep(0.1)
			count = 0
			while ser.in_waiting:
				ret = ser.read(ser.in_waiting)
				if cmd[0] == 'dump':
					for b in ret:
						print("%02x "%int(b), end='')
						count += 1
						if count % 8 == 0:
							print('')
				else:
					print(ret.decode('utf-8', "backslashreplace"), end='')
				sleep(0.1)
			print('\nok')
		elif cmd[0] == 'load':
			addr = int(cmd[1],16)
			if cmd[2].startswith('"'):
				q = line.find('"')
				hexbytes = []
				for c in line[q+1:]:
					if c == '"': break
					hexbytes.append(ord(c))
				hexbytes.append(0)
				length = len(hexbytes)
			else:
				length = int(cmd[2])
				hexbytes = [int(hb,16) for hb in cmd[3:]]
				if len(hexbytes) < length:
					hexbytes.extend([0] * (length - len(hexbytes)))
			data = [(addr >> 8), (addr & 255), (64+length)] + hexbytes
			cmd = bytes(data)
			# TODO split chunks for realy long data
			ser.write(cmd)
			while not ser.in_waiting:
				sleep(0.1)
			while ser.in_waiting:
				ret = ser.read(ser.in_waiting)
				# TODO match against input
				sleep(0.1)
			print('ok')
		elif cmd[0] == 'file':
			with open(cmd[1], 'rb') as f:
				hexbytes = f.read()
				length = len(hexbytes)
			addr = 0
			while length > 63:
				data = [(addr >> 8), (addr & 255), (64+63)]
				send = bytes(data)
				ser.write(send)
				while not ser.in_waiting:
					sleep(0.1)
				while ser.in_waiting:
					ret = ser.read(ser.in_waiting)
					# TODO match against input
					sleep(0.1)
				send = hexbytes[addr:addr+63]
				ser.write(send)
				while not ser.in_waiting:
					sleep(0.1)
				while ser.in_waiting:
					ret = ser.read(ser.in_waiting)
					# TODO match against input
					sleep(0.1)
				addr += 63
				length -= 63
			if length > 0:
				data = [(addr >> 8), (addr & 255), (64+length)]
				send = bytes(data)
				ser.write(send)
				while not ser.in_waiting:
					sleep(0.1)
				while ser.in_waiting:
					ret = ser.read(ser.in_waiting)
					# TODO match against input
					sleep(0.1)
				send = hexbytes[addr:addr+length]
				ser.write(send)
				while not ser.in_waiting:
					sleep(0.1)
				while ser.in_waiting:
					ret = ser.read(ser.in_waiting)
					# TODO match against input
					sleep(0.1)
			print('ok')
		elif cmd[0] in  {'run', 'runs'}:
			addr = int(cmd[1],16)
			data = [(addr >> 8), (addr & 255), (0xc0)]
			send = bytes(data)
			ser.write(send)
			while not ser.in_waiting:
				sleep(0.1)
			# TODO match against input bytes first
			ret = ser.read(3)
			while not ser.in_waiting:
				sleep(0.1)
			count = 0
			again = True
			while again:
				again = False
				while ser.in_waiting:
					ret = ser.read(ser.in_waiting)
					if cmd[0] == 'run':
						for b in ret:
							print("%02x "%int(b), end='')
							count += 1
							if count % 16 == 0:
								print('')
					else:
						print(ret.decode('utf-8', "backslashreplace"), end='')
					sleep(0.1)
				sleep(1.0) # timeout, we do not know when a program is going to end
				again = ser.in_waiting > 0
			print('\nok')

		else:
			print('unknown command', cmd[0])
