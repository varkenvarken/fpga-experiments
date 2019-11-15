SYN = yosys
PNR = arachne-pnr
GEN = icepack
PROG = iceprog 

TOP = puck.v 
PCF = icestick.pcf
DEVICE = 1k

OUTPUT = $(patsubst %.v,%.bin,$(TOP))

all: $(OUTPUT)

%.bin: %.tiles
	$(GEN) $< $@

%.tiles: %.blif
	$(PNR) -d $(DEVICE) -p $(PCF) -o $@ $<

%.blif: $(TOP)
	$(SYN) -q -p "read_verilog $<; hierarchy -libdir . ; synth_ice40 -flatten -blif $@"

clean:
	rm -f *.bin *.blif *.tiles

flash: $(OUTPUT)
	$(PROG) $<

.PHONY: all clean flash
