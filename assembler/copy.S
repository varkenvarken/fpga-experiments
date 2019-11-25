start: $100
	LDBASE0 line1
	LDBASE1 line2
	LDC #0
	LDD #0
loop:
	LDICP
	TSTA
	BRZ done:
	STIDP
	BRA loop
done:
	HLT

line1: $200
	BYTE0 "Hello world! Hello world! Hello world! Hello world! Hello world! Oink!"
line2: $280
	BYTE0 "xXxXxXxXxXxXxXxXxX"


