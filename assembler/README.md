assembler.py
============

synopsis
--------
    usage:
  
    python3 assembler.py [-h] [-p] [-l] [-d] [-v] [FILE [FILE ...]
  
    positional arguments:
      FILE            files to read, if empty, stdin is used

    optional arguments:
      -h, --help      show this help message and exit
    
      -p, --preamble  add puck monitor load code
    
      -l, --labels    print list of labels to stderr
    
      -d, --debug     dump internal code representation
    
      -v, --verbose   print annotated source code

typical use
-----------

    python3 assembler mycode.S > mycode.bin

This will assemble the code in mycode.S and put the resulting bytes into mycode.bin
Such a .bin file might be imported in monitor.py with 'file mycode.bin'

syntax
------
The assembler supports all opcodes currently implemented by puck. The list of opcodes is available from google sheets:

[opcodes](https://docs.google.com/spreadsheets/d/e/2PACX-1vSgl614HdDDAlUDg5i-s9ByjnLRYJEWqzRHlLzCsqVWnU_mfn5FWId8qTXAKgVFF7JwN4j8jRkzMf4Q/pubhtml)

it also supports labels (always on a line of their own):

    start: $100   // an label specifying a specific address
      hlt
     data:         // a label with an implicit address ($101 in this case because htl is a 1-byte opcode)
      byte 40
