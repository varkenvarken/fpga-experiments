module branchlogic(
	input [addr_width-1:0] addr,
	input [7:0] offset,
	input [1:0] condition,
	output [addr_width-1:0] result0,
	output [addr_width-1:0] resultc,
	output [addr_width-1:0] resultz,
	);
	parameter addr_width = 9;

	wire [addr_width-1:0] signextend;
	wire [addr_width-1:0] newaddr;
	assign signextend = {{(addr_width-8){offset[7]}},offset};
	assign newaddr = addr + signextend + {{(addr_width-1){1'b0}}, offset[7]};
	assign result0 = newaddr;
	assign resultc = condition[1] ? newaddr : addr; 
	assign resultz = condition[0] ? newaddr : addr; 

endmodule
