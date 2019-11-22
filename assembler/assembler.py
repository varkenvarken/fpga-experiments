#  bare bones assembler for puck cpu  (c) 2019 Michel Anders
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
#  


# Note that code is horrible kludge and about the worst example of
# clean code you can think of. I might rewrite this some time.

from argparse import ArgumentParser
import fileinput
import sys
import re

errors = 0
lineno = 0
address = 0
opcodes = {
	'LDA'	: {'imm': (0x80,2), 'zeropage': (0x84,2) },
	'HLT'	: {'implied': (0x00, 1) },
	'OUTA'	: {'implied': (0x01, 1) },
	'BRA'	: {'relative': (0x90, 2) },
	'LDBASE0': { 'long': (0xa0,2) },
	}

labels = {}
code = []

def init():
	pass

def stripcomment(line):
	c = line.find("//")
	if c >= 0 :
		line = line[:c]
	return line

linere = re.compile(r"(?P<Label>(?P<labelname>[A-Za-z_][A-Za-z_]*):(\s+(?P<labeldef>.*))?)|(?P<Mnemonic>(?P<mnemonicname>[A-Z][A-Z0-9]+)(\s+(?P<arg>(?P<imm>[#]\s*.+)|(?P<addr>[^#].*)))?)")

addrre = re.compile(r"(?P<Label>(?P<labelname>[A-Za-z_][A-Za-z_]*))|(?P<decimal>\d+)|(?P<hex>\$[01-9a-fA-F]+)")

def parseaddr(addr):
	m = addrre.match(addr)
	if m:
		groups = m.groupdict()
		if groups['Label']:
			if groups['labelname'] in labels:
				return labels[groups['labelname']],""
			else:
				labels[groups['labelname']] = None
				return (None,groups['labelname']),""
		elif groups['decimal']:
			return int(groups['decimal']),""
		elif groups['hex']:
			return int(groups['hex'][1:],16),""
	return None,"Syntax error in argument"

def parsevalue(value):
	value = value.strip()
	if value.startswith("$"):
		return int(value[1:],16)
	return int(value)

def process(line):
	global lineno
	global address
	global opcodes
	global errors

	errormsg = ""
	lineno += 1
	line = stripcomment(line).strip()
	if len(line) == 0: return

	m = linere.match(line)
	if m:
		groups = m.groupdict()
		if groups['Label']:
			if groups['labeldef']:
				address = parsevalue(groups['labeldef'])
			labels[groups['labelname']] = address
		elif groups['Mnemonic']:
			opcode = groups['mnemonicname']
			if opcode in opcodes:
				info = opcodes[opcode]
				arg = groups['arg']
				if arg:
					if groups['imm']:
						if 'imm' in info:
							value = parsevalue(groups['imm'][1:]) # strip leading hashmark #
							print("%04x %02x %s" % (address, info['imm'][0], groups['imm']), file=sys.stderr)
							code.append((address,info['imm'][0]))
							address += 1
							code.append((address,value))
							address += 1
						else:
							errors += 1
							errormsg = "%s does not have an implied addressing mode" % opcode
					else:
						addr, msg = parseaddr(groups['addr'])
						if addr is not None:
							if 'zeropage' in info:
								print("%04x %02x %s" % (address, info['zeropage'][0], groups['addr']), file=sys.stderr)
								code.append((address,info['zeropage'][0]))
								address += 1
								code.append((address,addr))
								address += 1
							elif 'relative' in info:
								print("%04x %02x %s" % (address, info['relative'][0], groups['addr']), file=sys.stderr)
								code.append((address,info['relative'][0]))
								address += 2
								if type(addr) is tuple: # unresolved label
									code.append((address,(addr,address)))
								else:
									code.append((address,addr - address))
							elif 'long' in info:
								print("%04x %02x %s" % (address, info['long'][0], groups['addr']), file=sys.stderr)
								if type(addr) is tuple: # unresolved label
									code.append((address,info['long'][0]))
									code.append((address+1,(addr,'LONG')))
								else:
									op1 = info['long'][0] + (addr >> 8)
									op2 = addr & 0xff
									code.append((address,op1))
									code.append((address+1,op2))
								address += 2
							else:
								errors += 1
								errormsg = "%s does not have a zeropage or relative addressing mode" % opcode
						else:
							errors += 1
							errormsg = msg
				else:
					if 'implied' in info:
						print("%04x %02x" % (address, info['implied'][0]), file=sys.stderr)
						code.append((address,info['implied'][0]))
						address += 1
					else:
						errors += 1
						errormsg = "%s does not have an implied addressing mode" % opcode
			else:
				errors += 1
				errormsg = "Unknown opcode"
		else:
			errors += 1
			errormsg = "Unknown error"
	else:
		errors += 1
		errormsg = "Syntax error"
	if errormsg != "":
		print(lineno, errormsg, file=sys.stderr)
		print(lineno,line, file=sys.stderr)

def resolve():
	global errors
	for i,(addr,c) in enumerate(code):
		if type(c) is tuple:
			if type(c[0]) is tuple:
				if c[0][1] in labels:
					if c[1] == 'LONG':
						code[i] = addr,(labels[c[0][1]] & 0xff)
						ap,cp = code[i-1] 
						code[i-1] = (ap,cp | (labels[c[0][1]] >> 8))
					else:
						code[i] = addr,labels[c[0][1]] - c[1]
				else:
					errors += 1
				print("unresolved label %s" % c[0][1], file=sys.stderr)
			else:
				if c[1] in labels:
					code[i] = addr,labels[c[1]]
				else:
					errors += 1
				print("unresolved label %s" % c[1], file=sys.stderr)

def fill():
	global code
	filled = []
	addr = 0
	for a,b in code:
		if a > addr:
			filled.extend([(0,0)] * (a-addr))
		filled.append((a,b))
		addr = a + 1
	code = filled

if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument('--dummy', help='dummy argument')
	parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
	args = parser.parse_args()

	init()
	for line in fileinput.input(files=args.files):
		process(line)

	resolve()

	print(labels, file=sys.stderr)
	print(code, file=sys.stderr)

	fill()

	nbytes = len(code)
	start = 0
	end = 63
	while end <= nbytes:
		sys.stdout.buffer.write(bytes([0,0,0x7f]))
		sys.stdout.buffer.write(bytes([c[1] if c[1] >= 0 else 256 + c[1] for c in code[start:end]]))
		start = end
		end += 63
	sys.stdout.buffer.write(bytes([0,0,0x40 + nbytes - start]))
	sys.stdout.buffer.write(bytes([c[1] if c[1] >= 0 else 256 + c[1] for c in code[start:nbytes]]))
