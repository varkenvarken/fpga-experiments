start: $100
	LDA #$15
	LDB #$25
	PUSHA
	PUSHB
	LDA #$1f
	LDB #$2f
	CALL showstack
here:
	POPA
	OUTA			// ouput $25
	POPA
	OUTA			// ouput $15
	HLT
showstack:
	LDA #1
	OUTA			// ouput $01
	LDAS #1
	OUTA			// ouput $0c  [lower 'here']
	LDA #2
	OUTA			// ouput $02
	LDAS #2
	OUTA			// ouput $01  [higher 'here']
	LDA #3
	OUTA			// ouput $03
	LDAS #3
	OUTA			// ouput $25   PUSHA
	LDA #4
	OUTA			// ouput $4
	LDAS #4
	OUTA			// ouput $15   PUSHB
	RET

