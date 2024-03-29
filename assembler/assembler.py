#  An assembler for the puck cpu  (c) 2019 Michel Anders
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

from argparse import ArgumentParser
import fileinput
import sys

class Opcode:
	def __init__(self, name, desc='', implied=None, imm=None, short=None, long=None, relative=None, 
					data=False, bytes=True, words=False, longs=False, addzero=True,
					userdefined=None):
					#check that mutually exclusive modes are flagged
		 self.name = name.upper()
		 self.desc = desc
		 self.implied = implied
		 self.imm = imm
		 self.short = short
		 self.long = long
		 self.relative = relative
		 self.data = data
		 self.bytes = bytes
		 self.words = words
		 self.longs = longs
		 self.addzero = addzero
		 self.userdefined = userdefined

	def code(self, operand, address, labels):
		imm = False
		if operand.startswith('#'):
			imm = True
			operand = operand[1:]
		if operand == '':
			value = None
		else:
			value = eval(operand,globals(),labels)
		if imm:
			if self.imm is None: raise NotImplementedError("%s does not support an immediate mode"%self.name)
			return self.imm.to_bytes(1,'big') + self.bytevalue(value) # checks if value fits 8 bit -128 : 255
		elif self.implied is not None:
			if value is not None: raise NotImplementedError("%s is implied and does not take an operand"%self.name)
			return self.implied.to_bytes(1,'big')
		elif self.short is not None:
			return self.short.to_bytes(1,'big') + self.bytevalue(value)  # checks if value fits 16 bit 0 : 2^16-1
		elif self.long is not None:  # the trick with the little conversion to two bytes of a single byte value actually moves the opcode to the high byte
			return self.bytes_or(self.long.to_bytes(2,'little'), self.longaddress(value))  # checks if value fits 13 bit  0 : 2^13-1
		elif self.relative is not None:
			return self.relative.to_bytes(1,'big') + self.signedbytevalue(value - (address+2)).to_bytes(1,'big', signed=True)  # checks if value fits 8 bit  -128 : 127
		elif self.data:
			if type(value) == str and self.bytes:
				values = bytes(value,'UTF-8')
				if self.addzero:
					values += b'\0'
				return values
			else:
				values = [eval(v, globals(), labels) for v in operand.split(',')]
				if self.addzero:
					values.append(0)
				if self.bytes:
					return b''.join(self.bytevalue(v) for v in values)
				elif self.words:
					return b''.join(self.wordvalue(v) for v in values)
				elif self.longs:
					return b''.join(self.longvalue(v) for v in values)
		else:
			raise NotImplementedError("%s no valid mode defined"%self.name)

	@staticmethod
	def bytes_or(a,b):
		return bytes(ba|bb for ba,bb in zip(a,b))

	@staticmethod
	def bytevalue(v):
		if type(v) == str:
			v = ord(v)
		if v < -128 or v > 255:
			raise ValueError()
		return v.to_bytes(1, 'big', signed=v<0)

	@staticmethod
	def wordvalue(v):
		if v < -2**15 or v > 2**16-1:
			raise ValueError()
		return v.to_bytes(2, 'big', signed=v<0)

	@staticmethod
	def longvalue(v):
		if v < -2**31 or v > 2**32-1:
			raise ValueError()
		return v.to_bytes(4, 'big', signed=v<0)

	@staticmethod
	def longaddress(v):    # long means fit for our address space of 8K i.e. 2^13
		if v < 0 or v > 2**13-1:
			raise ValueError()
		return v.to_bytes(2,'big')

	@staticmethod
	def signedbytevalue(v):
		if v < -128 or v > 127:
			raise ValueError(v)
		return v

	def length(self, operand):
		imm = False
		if operand.startswith('#'):
			return 2
		elif self.short is not None:
			return 2
		elif self.long is not None:
			return 2
		elif self.relative is not None:
			return 2
		elif self.data:
			if operand.strip().startswith('"'):
				nvalues = len(bytes(eval(operand),encoding='UTF-8'))
			else:
				nvalues = len(operand.split(','))
			if self.addzero:
				nvalues += 1
			if self.bytes:
				return nvalues
			elif self.words:
				return nvalues * 2
			elif self.longs:
				return nvalues * 4
		else:
			return 1

opcode_list = [
  Opcode(name='LDA', desc='A = [addr] , A = #value',
     imm=0x80, short=0x84),
  Opcode(name='LDB', desc='B = [addr] , B = # value',
     imm=0x81, short=0x85),
  Opcode(name='LDC', desc='C = [addr] , C = # value',
     imm=0x82, short=0x86),
  Opcode(name='LDD', desc='D = [addr] , D = # value',
     imm=0x83, short=0x87),
  Opcode(name='STA', desc='[addr] = A',
     short=0x88),
  Opcode(name='STB', desc='[addr] = B',
     short=0x89),
  Opcode(name='STC', desc='[addr] = C',
     short=0x8a),
  Opcode(name='STD', desc='[addr] = D',
     short=0x8b),
  Opcode(name='HLT', desc='Halt cpu',
     implied=0x00),
  Opcode(name='OUTA', desc='Serial Out = A',
     implied=0x01),
  Opcode(name='INA', desc='A = Serial In',
     implied=0x02),
  Opcode(name='CLF', desc='Clear flags',
     implied=0x03),
  Opcode(name='CNTRA', desc='A = Counter Register',
     implied=0x0f),
  Opcode(name='BRA', desc='Branch realative',
     relative=0x90),
  Opcode(name='BRZ', desc='Branch realative if zero flag set',
     relative=0x91),
  Opcode(name='BRC', desc='Branch realative if carry flag set',
     relative=0x92),
  Opcode(name='LDBASE0', desc='BASE0 = addr',
     long=0xa0),
  Opcode(name='LDBASE1', desc='BASE1 = addr',
     long=0xc0),
  Opcode(name='CALL', desc='[SP--].[SP--] = PC (Call subroutine, push return)',
     long=0xe0),
  Opcode(name='PUSHA', desc='[SP--] = A',
     implied=0x18),
  Opcode(name='PUSHB', desc='[SP--] = B',
     implied=0x19),
  Opcode(name='PUSHC', desc='[SP--] = C',
     implied=0x1a),
  Opcode(name='PUSHD', desc='[SP--] = D',
     implied=0x1b),
  Opcode(name='POPA', desc='A = [++SP]',
     implied=0x1c),
  Opcode(name='POPB', desc='B = [++SP]',
     implied=0x1d),
  Opcode(name='POPC', desc='C = [++SP]',
     implied=0x1e),
  Opcode(name='POPD', desc='D = [++SP]',
     implied=0x1f),
  Opcode(name='LDAS', desc='A = [SP + value]',
     imm=0x9c),
  Opcode(name='LDBS', desc='B = [SP + value]',
     imm=0x9d),
  Opcode(name='LDCS', desc='C = [SP + value]',
     imm=0x9e),
  Opcode(name='LDDS', desc='D = [SP + value]',
     imm=0x9f),
  Opcode(name='STAS', desc='[SP + value] = A',
     imm=0x94),
  Opcode(name='STBS', desc='[SP + value] = B',
     imm=0x95),
  Opcode(name='STCS', desc='[SP + value] = C',
     imm=0x96),
  Opcode(name='STDS', desc='[SP + value] = D',
     imm=0x97),
  Opcode(name='RET', desc='PC = [++SP],[++SP]  (return from call)',
     implied=0x10),
  Opcode(name='MOVAB', desc='B = A',
     implied=0x21),
  Opcode(name='MOVAC', desc='C = A',
     implied=0x22),
  Opcode(name='MOVAD', desc='D = A',
     implied=0x23),
  Opcode(name='MOVBA', desc='A = B',
     implied=0x24),
  Opcode(name='MOVCA', desc='A = C',
     implied=0x28),
  Opcode(name='MOVDA', desc='D = A',
     implied=0x2c),
  Opcode(name='LDIC', desc='A = [BASE0 + C]',
     implied=0x30),
  Opcode(name='LDICP', desc='A = [BASE0 + C++]',
     implied=0x32),
  Opcode(name='STID', desc='[BASE1 + D] = A',
     implied=0x39),
  Opcode(name='STIDP', desc='[BASE1 + D++] = A',
     implied=0x3b),
  Opcode(name='ADD', desc='A += B',
     implied=0x70),
  Opcode(name='ADC', desc='A += B + Carry',
     implied=0x71),
  Opcode(name='SUB', desc='A -= B',
     implied=0x72),
  Opcode(name='SBC', desc='A -= B - Carry',
     implied=0x73),
  Opcode(name='OR', desc='A |= B',
     implied=0x74),
  Opcode(name='AND', desc='A &= B',
     implied=0x75),
  Opcode(name='NOT', desc='A = ~A',
     implied=0x76),
  Opcode(name='XOR', desc='A ^= B',
     implied=0x77),
  Opcode(name='TSTA', desc='A = A (sets zero flag)',
     implied=0x78),
  Opcode(name='TSTB', desc='A = B (sets zero flag)',
     implied=0x79),
  Opcode(name='NEGA', desc='A = -A',
     implied=0x7a),
  Opcode(name='CMP', desc='A = A <=> B',
     implied=0x7b),
  Opcode(name='SHL', desc='A = A << 1',
     implied=0x7c),
  Opcode(name='SHR', desc='A = A >> 1',
     implied=0x7d),
  Opcode(name='SHLC', desc='A = A << 1, A[0] = Carry',
     implied=0x7e),
  Opcode(name='SHRC', desc='A = A >> 1, A[7] = Carry',
     implied=0x7f),
  Opcode(name='NOP', desc='Do nothing',
     implied=0x04),
  Opcode(name='BYTE', desc='define byte values (comma separated or string)',
     data=True, bytes=True , words=False, longs=False, addzero=False), 
  Opcode(name='BYTE0', desc='define byte values + extra nul (comma separated or string)',
     data=True, bytes=True , words=False, longs=False, addzero=True), 
  Opcode(name='WORD', desc='define word values (comma separated)',
     data=True, bytes=False, words=True , longs=False, addzero=False), 
  Opcode(name='WORD0', desc='define word values + extra nul (comma separated)',
     data=True, bytes=False, words=True , longs=False, addzero=True), 
  Opcode(name='LONG', desc='define long word values (comma separated)',
     data=True, bytes=False, words=False, longs=True , addzero=False), 
  Opcode(name='LONG0', desc='define long word values + extra nul (comma separated)',
     data=True, bytes=False, words=False, longs=True , addzero=True), 
]

opcodes = {op.name:op for op in opcode_list}
del opcode_list

def stripcomment(line):
	c1 = line.find("//")  # c++ convention
	c2 = line.find(";")  # asm convention

	if c1 < 0 :
		if c2 < 0:
			return line
		c = c2
	else:
		c = min(c1,c2) if c2 >= 0 else c1
	line = line[:c]
	return line

def assemble(lines, debug=False):
	errors = 0
	# pass1 determine label addresses
	labels={}
	addr=0
	processed_lines = []
	lineno = 1
	deflines = None
	defop = None
	while len(lines):
		filename, linenumber, line = lines.pop(0)
		line = stripcomment(line).strip()
		if line != '':
			elements = line.split(None,1)
			op = elements[0]
			operand = elements[1] if len(elements) > 1 else ''

			if deflines is not None:
				if op == '#end':
					opcodes[defop] = Opcode(name=defop, userdefined=deflines)
					deflines = None
					defop = None
				else:
					deflines.append((filename, linenumber, line))
				continue

			if op.endswith(':') or op.endswith('='):
				constant = op.endswith('=')
				label=op[:-1]
				if label in labels: warning('%s[%d]redefined label'%(filename,linenumber))
				if operand == '':
					if constant: warning('%s[%d]empty constant definition, default to addr'%(filename,linenumber))
					labels[label]=addr  # implicit label definition
				else:
					try:
						addr=eval(operand,globals(),labels)
						labels[label]=addr  # explicit label definition
					except:  #ignore undefined in the first pass
						pass
			elif op.startswith('#define'):
				defop = operand  # should check for non empty and not yet present
				deflines = list()
				continue
			else:
				try:
					opcode = opcodes[op.upper()]
					if opcode.userdefined != None:
						for ul in reversed(opcode.userdefined):
							lines.insert(0,ul)
						continue
					else:
						addr+=opcode.length(operand)  # this does also cover byte,byte0 and word,word0,long,long0 directives
				except KeyError:
					print("Error: %s[%d] unknown opcode %s"%(filename, linenumber, op), file=sys.stderr)
					continue
		processed_lines.append((filename, linenumber, line))

	#pass 2, label bit is the same except we generate errors when we cannot resolve
	code=bytearray()
	addr=0
	lines = processed_lines
	for filename, linenumber, line in lines:
		if debug : dline = "%s[%3d] %s"%(filename, linenumber, line.strip())
		line = stripcomment(line).strip()
		if line == '': continue
		elements = line.split(None,1)
		op = elements[0]
		operand = elements[1] if len(elements) > 1 else ''
		if op.endswith(':')  or op.endswith('='):
			constant = op.endswith('=')
			label=op[:-1]
			if operand == '':
				labels[label]=addr  # implicit label definition
			else:
				try:
					newaddr=eval(operand,globals(),labels)
					labels[label]=newaddr  # explicit label definition
				except Exception as e:
					print("Error: %s[%d] syntax error %s"%(filename, linenumber, operand), file=sys.stderr)
					continue
				if not constant:		# only labels update the current address and may fill intermediate space
					fill = newaddr - addr
					if fill < 0:
						warning('%s[%d]label %s defined to be at lower address than current'%(filename,linenumber,label))
					else:
						code.extend([0] * fill)
						addr = newaddr
			if debug : dcode = "%04x %s "%(addr, label)
		else:
			try:
				pp=opcodes[op.upper()]
				newcode=pp.code(operand, addr, labels)
				code.extend(newcode)
				if debug :
					if pp.data:
						a = addr
						dcode = ""
						for i in range(0, len(newcode), 8):
							dcode += "%04x %s\n"%(a, " ".join("%02x"%b for b in newcode[i:i+8]))
							a += 8
						dcode = dcode[:-1] + "  " + "".join(["   "] * ((8 - len(newcode)%8)%8))
					else:
						dcode = "%04x %s"%(addr, " ".join("%02x"%b for b in newcode))
				addr += len(newcode)
			except Exception as e:
				print("Error: %s[%d] %s %s"%(filename, linenumber, e.args[0], line), file=sys.stderr)
		if debug: print("%-30s %s"%(dcode, dline), file=sys.stderr)
	# return results as bytes
	return code, labels, errors

if __name__ == '__main__':
	parser = ArgumentParser()
	parser.add_argument('-p', '--preamble', help='add puck monitor load code', action="store_true")
	parser.add_argument('-l', '--labels', help='print list of labels to stderr', action="store_true")
	parser.add_argument('-u', '--usage', help='show allowed syntax and exit', action="store_true")
	parser.add_argument('-d', '--debug', help='dump internal code representation', action="store_true")
	parser.add_argument('files', metavar='FILE', nargs='*', help='files to read, if empty, stdin is used')
	args = parser.parse_args()

	if args.usage:
		for name in sorted(opcodes):
			print("%-7s %s"%(name, opcodes[name].desc))
		sys.exit(0)

	try:
		lines = [ (fileinput.filename(),fileinput.filelineno(),line) for line in fileinput.input(files=args.files) ]
	except FileNotFoundError as e:
		print(e, file=sys.stderr)
		sys.exit(2)

	code, labels, errors = assemble(lines, args.debug)

	if args.labels:
		for label in sorted(labels):
			print("%-20s %04x"%(label,labels[label]), file=sys.stderr)

	if errors == 0:
		nbytes = len(code)
		start = 0
		end = 63
		while end <= nbytes:
			if args.preamble: sys.stdout.buffer.write(bytes([(start>>8),(start&0xff),0x7f]))
			sys.stdout.buffer.write(code[start:end])
			start = end
			end += 63
		if args.preamble: sys.stdout.buffer.write(bytes([(start>>8),(start&0xff),0x40 + nbytes - start]))
		sys.stdout.buffer.write(code[start:nbytes])

	sys.exit(errors > 0)
