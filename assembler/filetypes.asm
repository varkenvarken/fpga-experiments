# For complete documentation of this file, please see Geany's main documentation
[styling]
# Edit these in the colorscheme .conf file instead
default=default
comment=comment_line
commentblock=comment
commentdirective=comment
number=number_1
string=string_1
operator=operator
identifier=identifier_1
cpuinstruction=keyword_1
mathinstruction=keyword_2
register=type
directive=preprocessor
directiveoperand=keyword_3
character=character
stringeol=string_eol
extinstruction=keyword_4

[keywords]
# all items must be in one line
# this is by default a very simple instruction set; not of Intel or so
instructions=lda ldb ldc ldd ldbase0 ldbase1 sta stb stc std ina outa clf hlt pusha pushb pushc pushd popa popb popc popd call ret ldas ldbs ldcs ldds add adc sub sbc and or xor neg not tsta tstb cmp shl shr shlc shrc bra brc brz movab movac movad movba movca movda ldic ldicp stid stidp
registers=
directives=byte byte0 word


[settings]
# default extension used when saving files
extension=S

# the following characters are these which a "word" can contains, see documentation
#wordchars=_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789

# single comments, like # in this file
comment_single=//
# multiline comments
#comment_open=
#comment_close=

# set to false if a comment character/string should start at column 0 of a line, true uses any
# indentation of the line, e.g. setting to true causes the following on pressing CTRL+d
	#command_example();
# setting to false would generate this
#	command_example();
# This setting works only for single line comments
comment_use_indent=false

# context action command (please see Geany's main documentation for details)
context_action_cmd=

[indentation]
#width=4
# 0 is spaces, 1 is tabs, 2 is tab & spaces
#type=1

[build_settings]
# %f will be replaced by the complete filename
# %e will be replaced by the filename without extension
# (use only one of it at one time)
compiler=nasm "%f"

