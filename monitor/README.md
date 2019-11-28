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

- **dump** \[ -d \[ -s \] \] \[ \<hexaddr\> \[ \<length\> \] \]

>dump <length> bytes at \<hexaddress\>. defaults to 48 bytes. Dump without address dumps from last known address. Will normally dump in hex, but there is an option for decimal and signed.

- **dumpw** \[ -d \[ -s \] \] \[ \<hexaddr\> \[ \<length\> \] \]

>dump <length> 16-bit words at \<hexaddress\>. defaults to 31 words. Dump without address dumps from last known address. Will normally dump in hex, but there is an option for decimal and signed.

- **dumpl** \[ -d \[ -s \] \] \[ \<hexaddr\> \[ \<length\> \] \]

>dump <length> 32-bit words at \<hexaddress\>. defaults to 15 bytes. Dump without address dumps from last known address. Will normally dump in hex, but there is an option for decimal and signed.

- **dumps** \<hexaddr\> \[ \<length\> \]

>dump \<length\> bytes at \<hexaddress\> as unicode characters. defaults to 48 bytes.

- **load** \<hexaddr\> ( \<byte\> ... | "string" )

>load bytes into memory starting at <hexaddress>. If given a string adds nul character at the end. 

- **loadw** \<hexaddr\> \<word\> ...

>load words into memory starting at <hexaddress>. 

- **loadl** \<hexaddr\> \<lword\> ...

>load 32-bit words into memory starting at <hexaddress>.

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
- Values to be loaded are specified in **decimal** unless prefixed with 0x or 0b.
- When running a program output is dumped on screen. However, if the
 running program stops emitting output for longer than 1 second, the run
 command will return while the program keeps on running. The **flush** command
 might then be used to retrieve any later output.

 
