monitor.py
==========

The **monitor.py** program simplifies working with the monitor code
built into the puck SOC.

It connects to /dev/ttyUSB1 with 9600 8-N-2 (currenlty hardcoded)

running
-------

	python3 monitor.py

commands
--------

- **dump <hexaddr> <length>
 dump <length> bytes at <hexaddress> as hex bytes

- **dumps <hexaddr> <length>
 dump <length> bytes at <hexaddress> as unicode characters

- **load <hexaddr> <length> <hexbyte> ...
  load <length> bytes in to memory starting at <hexaddress>

- **file <filename>
 load binary data from ,filename> starting at address 0000

- **run <hexaddr>
 run a program at <hexaddr> and show output as hex bytes

- **runs <hexaddr>
 run a program at <hexaddr> and show output as unicode characters

- **flush
 dump any remaining data in the receive buffer as hex bytes

- **exit
 exits the monitor (and closes the serial connection)

- **help
 shows help menu

caveats
-------

- Addresses are always expected to be hexadecimal digits.
- Lengths are always expected to be in decimal.
- Bytes to be loaded are specified in hexadecimal.
- When running a program output is dumped on screen. However, if the
 running program stops emitting output for longer than 1 second, the run
 command will return while the program keeps on running. The **flush**
 might then be used to retreive any later output.

 
