zeropage:		// a label with an implied address (o in this case because it is the first)
// most progs will start here because page zero is for easy storage
start: $100		// a label that sets an address
LDA #$77		// immediate hex
LDA #77			// immediate decimal
LDA #-1			// immediate negative decimal
LDA $40			// zeropage hex
LDA 40			// zeropage decimal
LDA zeropage	// zeropage known label
OUTA			// implied
end:			// a label for an address
HLT				// implied
BRA end			// branch to known label
BRA target		// branch to forward label ref
HLT
HLT
target:
HLT
LDBASE0 start	// long address mode to known label
LDBASE0 data	// long address mode to forward label ref
XXX				// unknown opcode
HLT
data:
HLT
