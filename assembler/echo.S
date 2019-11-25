start: $100
	LDBASE1 line
	CALL getline
	LDBASE0 line
	CALL print
	HLT

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

line: $200
	BYTE0 "Hello world!"

