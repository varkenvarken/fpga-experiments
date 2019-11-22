start: $100
	LDBASE0 hello
	CALL print
	LDBASE0 hello
	CALL print
	HLT
print:
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
hello: $200
	BYTE0 "Hello world!"
