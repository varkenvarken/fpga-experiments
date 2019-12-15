SYN = yosys
PNR = nextpnr-ice40
GEN = icepack
PROG = iceprog 

ROMGEN = python3 rom.py

TOP = puck.v

# icebreaker
PCF = icebreaker.pcf
DEVICE = --up5k
PACKAGE= sg48
# icestick
#PCF = icestick.pcf
#DEVICE = --hx1k
#PACKAGE= tq144

PLACER=heap

OUTPUT = $(patsubst %.v,%.bin,$(TOP))

all: $(OUTPUT)

%.bin: %.asc
	$(GEN) $< $@

%.asc: %.json $(PCF)
	$(PNR) $(DEVICE) --placer $(PLACER) --package $(PACKAGE) --json $< --pcf $(PCF) --asc $@

%.json: $(TOP) ram.v cpu.v alu.v branchlogic.v rom.v pll.v $(PCF)
	$(SYN) -q -p "read_verilog $<; hierarchy -libdir . ; synth_ice40 -flatten -json $@"

rom.v: rom.py
	$(ROMGEN) > $@

pll.v: Makefile
	icepll -i 12 -o 24 -f $@ -m

clean:
	rm -f *.bin *.blif *.tiles *.asc *.json

flash: $(OUTPUT)
	$(PROG) $<

.PHONY: all clean flash
