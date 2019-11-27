// completely combinatorial (no registers) implementation of an 8-bit ALU
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
	wire [8:0] add,adc,sub,sbc,extend,min_a,result, shiftl, shiftr, shiftlc, shiftrc;
	reg [8:0] result;
	wire [7:0] b_and,b_or,b_xor,b_not, cmp;

	assign add = {0, a} + {0, b};
	assign adc = add + { 8'd0, carry};
	assign sub = {0, a} - {0, b};
	assign sbc = sub - { 8'd0, carry};
	assign b_and = {0, a & b};
	assign b_or  = {0, a | b};
	assign b_xor = {0, a ^ b};
	assign b_not = {0,~a    };
	assign extend = {a[7],a};
	assign min_a = -extend;
	assign cmp = sub[8] ? 9'h1ff : sub == 0 ? 0 : 1;
	assign shiftl = {a[7:0],1'b0};
	assign shiftr = {a[0],1'b0,a[7:1]};
	assign shiftlc = {a[7:0],carry};
	assign shiftrc = {a[0],carry,a[7:1]};

//	assign result = op[3:2] == 0 ? // addition/subtraction
//									( op[1] ? ( op[0] ? sbc : sub ): ( op[0] ? adc : add ) )
//				:(	op[3:2] == 1 ? // bitwise logic
//									( op[1] ? ( op[0] ? b_xor : b_not ): ( op[0] ? b_and : b_or ) )
//				:(	op[3:2] == 2 ? // test, invert, compare
//									( op[1] ? ( op[0] ? cmp : min_a ): ( op[0] ? {0, b} : {0, a} ) )
//								   // shifts
//				: 					( op[1] ? ( op[0] ? shiftrc : shiftlc ): ( op[0] ? shiftr : shiftl ) ) ) );

	always @(*) begin
	case (op)
		0: result <= add;
		1: result <= adc;
		2: result <= sub;
		3: result <= sbc;
		4: result <= b_or;
		5: result <= b_and;
		6: result <= b_not;
		7: result <= b_xor;
		8: result <= {0, a};
		9, //: result <= {0, b};
		10, //: result <= min_a;
		11: result <= cmp;
		12: result <= shiftl;
		13: result <= shiftl;
		14: result <= shiftlc;
		15: result <= shiftrc;
	endcase
	end

	assign c = result[7:0];
	assign carry_out = result[8];
	assign zero = (c == 0);

endmodule
