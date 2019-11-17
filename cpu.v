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

	reg [8:0] pc;
	reg [7:0] opcode, operand, outbyte;
	reg [7:0] A;

	wire hlt = opcode == 8'h00;
	wire one = opcode[7] == 0;

	localparam START  = 4'd0;
	localparam FETCH  = 4'd1;
	localparam DECODE = 4'd2;
	localparam OPLOAD = 4'd3;
	localparam ECHO   = 4'd4;
	localparam ECHO1  = 4'd5;
	localparam WAIT   = 4'd6;
	localparam WAIT2  = 4'd7;
	localparam OPLOAD2= 4'd8;
	localparam DECODE2= 4'd9;
	reg [3:0] state = START;

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
							state <= WAIT; // wait state is needed because ram is read on next cycle so dat will be available on next cycle + 1
						end
			WAIT	:	state <= OPLOAD;
			OPLOAD	:	begin
							opcode <= dread;
							pc <= pc + 1;
							state <= DECODE;
						end
			DECODE	:	begin
							c_raddr <= pc;
							if (hlt) begin // HLT
								state <= START;
								halted <= 1;
								led <= 0;
							end else if (one) begin // 1 byte opcode
								case (opcode[6:0])
									7'd1	:	state <= ECHO;	// OUTA
									default	:	state <= FETCH; // ignore all undefined 1 byte opcodes
								endcase
							end else begin			// 2 byte opcode
								state <= WAIT2;
							end
						end
			WAIT2	:	state <= OPLOAD2;
			OPLOAD2	:	begin
							operand <= dread;
							pc <= pc + 1;
							state <= DECODE2;
						end
			DECODE2	:	begin
							case (opcode[6:0])
								7'd0	:	begin	// LDA immediate
												A <= operand;
												state <= FETCH;
											end
								default	:	state <= FETCH; // ignore all undefined 2 byte opcodes
							endcase
						end
			ECHO	:	begin
							outbyte <= A;
							state <= ECHO1;
						end
			ECHO1	:	begin
							if(!is_transmitting) begin
								tx_byte <= outbyte;
								transmit <= 1;
								state <= FETCH;
							end
						end
		endcase
	end

endmodule
