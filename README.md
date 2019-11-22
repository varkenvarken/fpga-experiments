# fpga-experiments
Some verilog designs for an icestick40

puck: yet another 8-bit cpu on a small fpga


with fpgas [https://en.m.wikipedia.org/wiki/Field-programmable_gate_array] becoming cheaper, more convenient [http://www.latticesemi.com/icestick] and easier to program [http://www.clifford.at/yosys/] I wanted to try my hand at designing an 8-bit cpu. For no particular reason, just out of curiosity :-)

there have been plenty of inspirational projects ([https://github.com/jamesbowman/swapforth],[https://bitbucket.org/linuxlalala/nopcpu/src/master/]) but I wanted to start from scratch a document my findings, especially those related to Verilog [https://www.doulos.com/knowhow/verilog_designers_guide/what_is_verilog/], the hardware description language I have chosen to define my CPU with.

my development platform consists of:

- yosys/icestorm on Ubuntu
  I won't decument the installation process. just check the Icestorm site [http://www.clifford.at/icestorm/] and follow the instructions and the components will work out of the box

- a Lattice IceStick
  pretty powerful (should be able to run at clockspeeds well over 100 MHz), affordable and easy to use with its USB connector. it is not really large but big enough to implement an 8-bit processor, complete with ram, a serial interface (uart) and a small monitor mode to load/save data to memory and start a program

goals

- an 8-bit cpu
this the main goal and for me the fun part: designing and implementing a decent instruction set. Not just an ALU [wikipedia link] but also branch instructions and a return stack so that we can write subroutines.

- a monitor program
a monitor program is some hardware that allows you to inspect memory, upload bytes and run a program. you could of course create your hardware with a fixed program in rom but in my thinking a monitor program is essential for testing your designs quickly. That's why this component was actually the first i implemented.

it comes in two parts: hardware to load and dump memory contents, and a python program to make life a bit easier.
The hardware is mainly about reusing an existing uart design [link] and making our first steps into Verilog.

- an assembler
writing any kind of machine code by hand quickly becomes unwieldy and error prone. so an assembler, even a rather simplistic one, is a must have. Writing one in Python is straightforward so i'll certainly create one.

- documentation
I mention this as a goal in itself because for me it is important to understand whatever I find out so that others (or myself at a later point) do not have to reinvent the wheel

- and finally, a calculator program
it will read input lines, parse numbers and operators amd perform simple calculations


