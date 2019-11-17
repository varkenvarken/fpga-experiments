module alu(
	input [7:0] a,
	input [7:0] b,
	input carry,
	input [3:0] op,
	output [7:0] c,
	output carry_out,
	output zero
	);

	wire [8:0] result;
	assign result = {0, a} + {0, b} + { 8'd0, carry};  
	assign carry_out = result[8];
	assign c = result[7:0];
	assign zero = (c == 0);

endmodule
