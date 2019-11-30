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
	'LDA'		: {'imm'	 : (0x80, 2),	'zeropage': (0x84, 2) },
	'LDB'		: {'imm'	 : (0x81, 2),	'zeropage': (0x85, 2) },
	'LDC'		: {'imm'	 : (0x82, 2),	'zeropage': (0x86, 2) },
	'LDD'		: {'imm'	 : (0x83, 2),	'zeropage': (0x87, 2) },
	'STA'		: {'zeropage': (0x88, 2) },
	'STB'		: {'zeropage': (0x89, 2) },
	'STC'		: {'zeropage': (0x8a, 2) },
	'STD'		: {'zeropage': (0x8b, 2) },
	'HLT'		: {'implied' : (0x00, 1) },
	'OUTA'		: {'implied' : (0x01, 1) },
	'INA'		: {'implied' : (0x02, 1) },
	'CLF'		: {'implied' : (0x03, 1) },
	'CNTRA'		: {'implied' : (0x0f, 1) },
	'BRA'		: {'relative': (0x90, 2) },
	'BRZ'		: {'relative': (0x91, 2) },
	'BRC'		: {'relative': (0x92, 2) },
	'LDBASE0'	: {'long'	 : (0xa0, 2) },
	'LDBASE1'	: {'long'	 : (0xc0, 2) },
	'CALL'		: {'long'	 : (0xe0, 2) },
	'PUSHA'		: {'implied' : (0x18, 1) },
	'PUSHB'		: {'implied' : (0x19, 1) },
	'PUSHC'		: {'implied' : (0x1a, 1) },
	'PUSHD'		: {'implied' : (0x1b, 1) },
	'POPA'		: {'implied' : (0x1c, 1) },
	'POPB'		: {'implied' : (0x1d, 1) },
	'POPC'		: {'implied' : (0x1e, 1) },
	'POPD'		: {'implied' : (0x1f, 1) },
	'LDAS'		: {'imm'	 : (0x9c, 2) },
	'LDBS'		: {'imm'	 : (0x9d, 2) },
	'LDCS'		: {'imm'	 : (0x9e, 2) },
	'LDDS'		: {'imm'	 : (0x9f, 2) },
	'STAS'		: {'imm'	 : (0x94, 2) },
	'STBS'		: {'imm'	 : (0x95, 2) },
	'STCS'		: {'imm'	 : (0x96, 2) },
	'STDS'		: {'imm'	 : (0x97, 2) },
	'RET'		: {'implied' : (0x10, 1) },
	'MOVAB'		: {'implied' : (0x21, 1) },
	'MOVAC'		: {'implied' : (0x22, 1) },
	'MOVAD'		: {'implied' : (0x23, 1) },
	'MOVBA'		: {'implied' : (0x24, 1) },
	'MOVCA'		: {'implied' : (0x28, 1) },
	'MOVDA'		: {'implied' : (0x2c, 1) },
	'LDIC'		: {'implied' : (0x30, 1) },
	'LDICP'		: {'implied' : (0x32, 1) },
	'STID'		: {'implied' : (0x39, 1) },
	'STIDP'		: {'implied' : (0x3b, 1) },
	'ADD'		: {'implied' : (0x70, 1) },
	'ADC'		: {'implied' : (0x71, 1) },
	'SUB'		: {'implied' : (0x72, 1) },
	'SBC'		: {'implied' : (0x73, 1) },
	'OR'		: {'implied' : (0x74, 1) },
	'AND'		: {'implied' : (0x75, 1) },
	'NOT'		: {'implied' : (0x76, 1) },
	'XOR'		: {'implied' : (0x77, 1) },
	'TSTA'		: {'implied' : (0x78, 1) },
	'TSTB'		: {'implied' : (0x79, 1) },
	'NEGA'		: {'implied' : (0x7a, 1) },
	'CMP'		: {'implied' : (0x7b, 1) },
	'SHL'		: {'implied' : (0x7c, 1) },
	'SHR'		: {'implied' : (0x7d, 1) },
	'SHLC'		: {'implied' : (0x7e, 1) },
	'SHRC'		: {'implied' : (0x7f, 1) },
	'BYTE'		: {'data'	 : (1,0)},
	'BYTE0'		: {'data'	 : (1,1)},
	'WORD'		: {'data'	 : (2,0)},
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

linere = re.compile(r"(?P<Label>(?P<labelname>[A-Za-z_][A-Za-z_0-9]*):(\s+(?P<labeldef>.*))?)|(?P<Mnemonic>(?P<mnemonicname>[A-Za-z][A-Za-z0-9]+)(\s+(?P<arg>(?P<imm>[#]\s*.+)|(?P<addr>[^#].*)))?)")

addrre = re.compile(r"(?P<Label>(?P<labelname>[A-Za-z_][A-Za-z_0-9]*))|(?P<decimal>\d+)|(?P<hex>\$[01-9a-fA-F]+)")

def parseaddr(addr):
	m = addrre.match(addr)
	if m:
		groups = m.groupdict()
		
		if groups['Label']:
			if groups['labelname'] in labels and labels[groups['labelname']] is not None:
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

def parsestring(s):
	data = []
	esc = False
	for c in s[1:]:
		if c in '\\' and not esc:
			esc = True
			continue
		elif c == '"' and not esc:
			esc = True
			continue
		esc = False
		data.append(ord(c))
	return data

def process(line, echo=False):
	global lineno
	global address
	global opcodes
	global errors

	errormsg = ""
	lineno += 1
	line = stripcomment(line).strip()
	if len(line) == 0: return errormsg, lineno

	m = linere.match(line)
	if m:
		groups = m.groupdict()
		if groups['Label']:
			if groups['labeldef']:
				address = parsevalue(groups['labeldef'])
			labels[groups['labelname']] = address
			if echo: print("%03d %04x %-23s %s" % (lineno, address, groups['labelname'], line), file=sys.stderr)
		elif groups['Mnemonic']:
			opcode = groups['mnemonicname'].upper()
			if opcode in opcodes:
				info = opcodes[opcode]
				arg = groups['arg']
				if arg:
					if groups['imm']:
						if 'imm' in info:
							value = parsevalue(groups['imm'][1:]) # strip leading hashmark #
							if echo: print("%03d %04x %02x %-20s %s" % (lineno, address, info['imm'][0], groups['imm'], line), file=sys.stderr)
							code.append((address,info['imm'][0]))
							address += 1
							code.append((address,value))
							address += 1
						else:
							errors += 1
							errormsg = "%s does not have an implied addressing mode" % opcode
					elif 'data' in info:
						nbytes,zero = info['data']
						if arg.startswith('"'):
							data = parsestring(arg)
						else:
							data = [parsevalue(a.strip()) for a in arg.split(",")]
						if nbytes == 1 and any( (d>255 or d < -128) for d in data):
							errors += 1
							errormsg = "Data definition for word contains out of bound bytes"
						else:
							startaddress = address
							start = len(code)
							if nbytes == 1:
								for d in data:
									code.append((address, d))
									address += 1
							else:
								for d in data:
									code.append((address, (d>>8)))
									address += 1
									code.append((address, (d & 0xff)))
									address += 1
							if zero:
								code.append((address, 0))
								address += 1
							end = len(code)
							if echo: 
								if nbytes > 1:
									#for i in range(start,end,2):
									#	print(code[i][1],code[i+1][1], file=sys.stderr)
									hexx = " ".join(["%02x%02x"%(code[i][1] if code[i][1] >=0 else 256 + code[i][1],code[i+1][1]) for i in range(start,end,2)])
								else:
									hexx = " ".join(["%02x"%code[i][1] for i in range(start,end)])
								print("%03d %04x %-45s %s" % (lineno, startaddress, hexx, line), file=sys.stderr)
					else:
						addr, msg = parseaddr(groups['addr'])
						if addr is not None:
							if 'zeropage' in info:
								if echo: print("%03d %04x %02x %-20s %s" % (lineno, address, info['zeropage'][0], groups['addr'], line), file=sys.stderr)
								code.append((address,info['zeropage'][0]))
								address += 1
								code.append((address,addr))
								address += 1
							elif 'relative' in info:
								if echo: print("%03d %04x %02x %-20s %s" % (lineno, address, info['relative'][0], groups['addr'], line), file=sys.stderr)
								code.append((address,info['relative'][0]))
								address += 1
								if type(addr) is tuple: # unresolved label
									code.append((address,(addr,address)))
								else:
									code.append((address,(addr - address)-1))
								address += 1
							elif 'long' in info:
								if echo: print("%03d %04x %02x %-20s %s" % (lineno, address, info['long'][0], groups['addr'], line), file=sys.stderr)
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
						if echo: print("%03d %04x %02x %-20s %s" % (lineno, address, info['implied'][0],"", line), file=sys.stderr)
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
	return errormsg, lineno

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
						code[i] = addr,(labels[c[0][1]] - c[1])-1
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
	parser.add_argument('-p', '--preamble', help='add puck monitor load code', action="store_true")
	parser.add_argument('-l', '--labels', help='print list of labels to stderr', action="store_true")
	parser.add_argument('-d', '--debug', help='dump internal code representation', action="store_true")
	parser.add_argument('-v', '--verbose', help='print annotated source code', action="store_true", default=False)
	parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
	args = parser.parse_args()

	for line in fileinput.input(files=args.files):
		error,lineno = process(line, args.verbose)
		if error != "":
			print("%s:%d ERROR: %s %s"%(fileinput.filename(),lineno,error,line.strip()), file=sys.stderr)

	resolve()

	if args.debug:
		for c in code:
			print("%04x %s" % c, file=sys.stderr)

	if args.labels:
		for label in sorted(labels):
			print("%-20s %s"%(label,labels[label]), file=sys.stderr)

	fill()

	nbytes = len(code)
	start = 0
	end = 63
	while end <= nbytes:
		if args.preamble: sys.stdout.buffer.write(bytes([(start>>8),(start&0xff),0x7f]))
		sys.stdout.buffer.write(bytes([c[1] if c[1] >= 0 else 256 + c[1] for c in code[start:end]]))
		start = end
		end += 63
	if args.preamble: sys.stdout.buffer.write(bytes([(start>>8),(start&0xff),0x40 + nbytes - start]))
	sys.stdout.buffer.write(bytes([c[1] if c[1] >= 0 else 256 + c[1] for c in code[start:nbytes]]))

	sys.exit(errors > 0)
