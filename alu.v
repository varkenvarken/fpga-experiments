module alu(
	input [7:0] a,
	input [7:0] b,
	input carry,
	input [3:0] op,
	output [7:0] c,
	output carry_out,
	output zero
	);

	// TODO: overflow/underflow
	wire [8:0] add,adc,sub,sbc,result;
	assign add = {0, a} + {0, b};
	assign adc = add + { 8'd0, carry};
	assign sub = {0, a} - {0, b};
	assign sbc = add - { 8'd0, carry};
	assign result = op[3:2] ? {0, a} : op[1]? ( op[0] ? sbc : sub ): ( op[0] ? adc : add ); // all undefined opcodes simply pass A thru
	assign carry_out = result[8];
	assign c = result[7:0];
	assign zero = (c == 0);

endmodule
