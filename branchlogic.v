module branchlogic(
	input [8:0] addr,
	input [7:0] offset,
	input [1:0] condition,
	output [8:0] result0,
	output [8:0] resultc,
	output [8:0] resultz,
	);

	wire [8:0] signextend;
	wire [8:0] newaddr;
	assign signextend = {offset[7],offset};
	assign newaddr = addr + signextend + {8'd0, offset[7]};
	assign result0 = newaddr;
	assign resultc = condition[1] ? newaddr : addr; 
	assign resultz = condition[0] ? newaddr : addr; 

endmodule
