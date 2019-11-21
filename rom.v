
module rom16x4 (
	input [3:0] addr, 
	input clk,
	output [3:0] data);

    wire [7:0] rdata;
	wire [15:0] RDATA;
	wire RCLK;
	wire [10:0] RADDR;

	SB_RAM40_4K #(
		.WRITE_MODE(1), 
		.READ_MODE(1),
    .INIT_0(256'h0055005400510050004500440041004000150014001100100005000400010000),
    .INIT_1(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_2(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_3(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_4(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_5(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_6(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_7(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_8(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_9(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_A(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_B(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_C(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_D(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_E(256'h0000000000000000000000000000000000000000000000000000000000000000),
    .INIT_F(256'h0000000000000000000000000000000000000000000000000000000000000000)
	) rom(
		.RDATA(RDATA),
		.RCLK(RCLK),
		.RCLKE(1),
		.RE(1),
		.RADDR(RADDR),
		.WCLK(0),
		.WCLKE(0),
		.WE(0),
		.WADDR(11'hxxxx),
		.MASK(16'hxxxx),
		.WDATA(8'hxx)
	);

    assign rdata =  {RDATA[14],RDATA[12],RDATA[10],RDATA[8],RDATA[6],RDATA[4],RDATA[2],RDATA[0]};
	assign data = rdata[3:0];
	assign RADDR = {7'b0, addr};
	assign RCLK = clk;

endmodule

