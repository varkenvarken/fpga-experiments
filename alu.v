module alu(
	input [7:0] a,
	input [7:0] b,
	input carry,
	input [3:0] op,
	output [7:0] c,
	output carry_out,
	output zero
	);

	wire [8:0] add,adc,result;
	assign add = {0, a} + {0, b};
	assign adc = add + { 8'd0, carry};
	assign result = op[3:1] ? {0, a} : ( op[0] ? adc : add ); // all undefined opcodes simply pass A thru
	assign carry_out = result[8];
	assign c = result[7:0];
	assign zero = (c == 0);

endmodule
