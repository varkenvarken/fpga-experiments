module cpu(
	input rst,
	input clk,
	input [7:0] dread, // from ram
	output reg [8:0] c_raddr,
	output reg [8:0] c_waddr,
	output reg [7:0] dwrite, // to ram
	output reg write_en,
	output reg led,
	output reg [7:0] tx_byte, 
	output reg transmit, 
	input is_transmitting,
	output reg halted,
	input [8:0] startaddr
	);

	reg [8:0] pc, memreg;
	reg [7:0] opcode, operand, outbyte;

	localparam START = 3'd0;
	localparam FETCH = 3'd1;
	localparam DECODE= 3'd2;
	localparam OPLOAD= 3'd3;
	localparam ECHO  = 3'd4;
	localparam ECHO1 = 3'd5;
	localparam WAIT  = 3'd6;
	localparam WAIT2 = 3'd7;
	reg [2:0] state = START;

	always @(posedge clk)
	begin
		led <= 0;
		write_en <= 0;
		transmit <= 0;
		halted <= 0;

		case(state)
			START	:	if(rst) begin 
							pc <= startaddr;
							state <= FETCH;
							led <= 1;
						end
			FETCH	:	begin
							c_raddr <= pc; 
							state <= WAIT2;
						end
			WAIT2	:	state <= OPLOAD;
			OPLOAD	:	begin
							opcode <= dread;
							pc <= pc + 1;
							state <= DECODE;
						end
			DECODE	:	begin
							state <= (opcode == 8'h00) ? START : ECHO;
							halted <= (opcode == 8'h00);
							led <= (opcode != 8'h00);
						end
			ECHO	:	begin
							outbyte <= opcode;
							state <= ECHO1;
						end
			ECHO1	:	begin
							if(!is_transmitting) begin
								tx_byte <= outbyte;
								transmit <= 1;
								state <= WAIT;
							end
						end
			WAIT	:	begin
							state <= FETCH;
						end
		endcase
	end

endmodule
