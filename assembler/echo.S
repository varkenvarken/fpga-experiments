start: $100
	LDBASE1 line
	CALL getline
	LDBASE0 line
	CALL print
	HLT

// keep echoing lines until empty line
continuousecho: $200
	LDBASE1 line
	CALL getline
	LDBASE0 line
	CALL print
	LDBASE0 line
	CALL strlen
	BRZ continuousechodone
	BRA continuousecho
continuousechodone:
	LDBASE0 linedone
	CALL print
	HLT

lib: $300
print: // print nul terminated string pointed to by base0
	LDA #0
	MOVAC
printget:
	LDICP
	TSTA
	BRZ printdone
	OUTA
	BRA printget
printdone:
	LDA #10 // add linefeed
	OUTA
	RET

getline: // store input a location pointed to by base1, stop on LF
	LDD #0
getchar:
	INA
	MOVAC
	LDB #10 // a linefeed character
	CMP		// comparing overwrites A
	MOVCA
	BRZ getlinedone
	STIDP
	BRA getchar
getlinedone:
	LDA #0
	STID
	RET

strlen: $400 // get length of nul terminated string pointed to by base0; returns length in A and zero flag set if a == 0
	LDA #0
	MOVAC
strlenget:
	LDICP
	TSTA
	BRZ strlendone
	BRA strlenget
strlendone:
	MOVCA
	LDB #1
	SUB
	RET

linedone:
	BYTE0 "done."
line: $500
	BYTE 0

