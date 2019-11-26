monitor.py
==========

The **monitor.py** program simplifies working with the monitor code
built into the puck SOC.

It connects to **/dev/ttyUSB1** with **9600 8-N-2** (currently hardcoded)

running
-------

	python3 monitor.py

commands
--------

- **dump** \[ \<hexaddr\> \[ \<length\> \] \]

>dump <length> bytes at \<hexaddress\> as hex bytes. defaults to 48 bytes. Dump without address dumps from last known address.

- **dumps** \<hexaddr\> \[ \<length\> \]

>dump \<length\> bytes at \<hexaddress\> as unicode characters. defaults to 48 bytes.

- **load** \<hexaddr\> ( \<byte\> ... | "string" )

>load bytes in to memory starting at <hexaddress>. If given a string adds nul character at the end.

- **file** \<filename\>

>load binary data from \<filename\> into memory starting at address 0000

- **run** \<hexaddr\>

>run a program at <hexaddr> and show output as hex bytes

- **runs** \<hexaddr\>

>run a program at \<hexaddr\> and show output as unicode characters

- **test** \<hexaddr\> (\<byte\> ... | "string" )

>checks whether memory at \<hexaddr\> contains the given bytes

- **flush**

>dump any remaining data in the receive buffer as hex bytes

- **exit**

>exits the monitor (and closes the serial connection)

- **help**

>shows help menu

caveats
-------

- Addresses are **alway**s expected to be hexadecimal digits.
- Bytes to be loaded are specified in **decimal** unless prefixed with 0x or 0b.
- When running a program output is dumped on screen. However, if the
 running program stops emitting output for longer than 1 second, the run
 command will return while the program keeps on running. The **flush** command
 might then be used to retreive any later output.

 
