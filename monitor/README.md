monitor.py
==========

The **monitor.py** program simplifies working with the monitor code
built into the puck SOC.

It connects to a serial port with **9600baud 8-N-2** (currently hardcoded)

running
-------

	python3 monitor.py [-i] [serialdevice]
	
	-i detect an iCEstick serial interface
	
	default serialdevice is /dev/ttyUSB1

commands
--------

- **dump** \[ -d \[ -s \] \] \[ *hexaddr* \[ *length* \] \]

>dump *length* bytes at *hexaddress*. defaults to 48 bytes. Dump without address dumps from last known address. Will normally dump in hex, but there is an option for decimal and signed.

- **dumpw** \[ -d \[ -s \] \] \[ *hexaddress* \[ *length* \] \]

>dump <length> 16-bit words at *hexaddress*. defaults to 31 words. Dump without address dumps from last known address. Will normally dump in hex, but there is an option for decimal and signed.

- **dumpl** \[ -d \[ -s \] \] \[ *hexaddress* \[ *length* \] \]

>dump <length> 32-bit words at *hexaddress*. defaults to 15 words. Dump without address dumps from last known address. Will normally dump in hex, but there is an option for decimal and signed.

- **dumps** *hexaddress* \[ *length* \]

>dump *length* bytes at *hexaddress* as unicode characters. defaults to 48 bytes.

- **load** *hexaddress* ( *byte* ... | "string" )

>load bytes into memory starting at *hexaddress*. If given a string adds nul character at the end. 

- **loadw** *hexaddress* *word* ...

>load words into memory starting at *hexaddress*. 

- **loadl** *hexaddress* *lword* ...

>load 32-bit words into memory starting at *hexaddress*.

- **file** *filename*

>load binary data from *filename* into memory starting at address 0000

- **run** *hexaddress*

>run a program at *hexaddress* and show output as hex bytes

- **runs** *hexaddress*

>run a program at *hexaddress* and show output as unicode characters

- **test** *hexaddress* ( *byte* ... | "string" )

>checks whether memory at *hexaddress* contains the given bytes

- **runp** *hexaddress*

>run program at *hexaddress* with a separate read process, showing output as hexbytes
>Ctrl-C ends connection

- **runps** *hexaddress* \[ *-t* \]

>run program at *hexaddress* with a separate read process, showing output as unicode strings
>Ctrl-C ends connection

- **flush**

>dump any remaining data in the receive buffer as hex bytes

- **exit**

>exits the monitor (and closes the serial connection)

- **break**

>dump any remaining characters in receive buffer and send break.

- **help**

>shows help menu

caveats
-------

- Addresses are **always** expected to be hexadecimal digits.
- Values to be loaded are specified in **decimal** unless prefixed with 0x or 0b.
- When running a program with **run** or **runs** output is dumped on screen. However, if the
 running program stops emitting output for longer than 1 second, the run
 command will return while the program keeps on running. The **flush** command
 might then be used to retrieve any later output.
 For continous interaction use **runps**

 
