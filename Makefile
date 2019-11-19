SYN = yosys
PNR = nextpnr-ice40
GEN = icepack
PROG = iceprog 

TOP = puck.v
PCF = icestick.pcf
DEVICE = --hx1k
PACKAGE= tq144
PLACER=heap

OUTPUT = $(patsubst %.v,%.bin,$(TOP))

all: $(OUTPUT)

%.bin: %.asc
	$(GEN) $< $@

%.asc: %.json
	$(PNR) $(DEVICE) --placer $(PLACER) --package $(PACKAGE) --json $< --pcf $(PCF) --asc $@

%.json: $(TOP) ram.v cpu.v alu.v branchlogic.v
	$(SYN) -q -p "read_verilog $<; hierarchy -libdir . ; synth_ice40 -flatten -json $@"

clean:
	rm -f *.bin *.blif *.tiles *.asc *.json

flash: $(OUTPUT)
	$(PROG) $<

.PHONY: all clean flash
