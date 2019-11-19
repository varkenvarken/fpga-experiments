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
	wire [7:0] b_and,b_or,b_xor,b_not;
	assign add = {0, a} + {0, b};
	assign adc = add + { 8'd0, carry};
	assign sub = {0, a} - {0, b};
	assign sbc = add - { 8'd0, carry};
	assign b_and = {0, a & b};
	assign b_or  = {0, a | b};
	assign b_xor = {0, a ^ b};
	assign b_not = {0,~a    };
	assign result = op[3:2] == 0 ? // addition/subtraction
									( op[1] ? ( op[0] ? sbc : sub ): ( op[0] ? adc : add ) )
				:	op[3:2] == 1 ? // bitwise logic
									( op[1] ? ( op[0] ? b_xor : b_not ): ( op[0] ? b_and : b_or ) )
				: {0, a} ; // all undefined opcodes simply pass A thru
	assign carry_out = result[8];
	assign c = result[7:0];
	assign zero = (c == 0);

endmodule
