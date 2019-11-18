`include "alu.v"

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
	input [8:0] startaddr,
	input received,
	input [7:0] rx_byte
	);

	reg [8:0] pc;
	reg [7:0] opcode, operand, outbyte;
	reg [7:0] A,B,C;
	reg [1:0] flags;
	wire [7:0] result;
	wire c_out, zero;
	wire [8:0] jmpaddress, jmpaddressc, jmpaddressz;
	wire branchcondition;

	alu alu0(
		.a(A),
		.b(B),
		.carry(flags[1]),
		.op(0),
		.c(result),
		.carry_out(c_out),
		.zero(zero)
		);

	branchlogic branchlogic0(pc, operand, flags, jmpaddress, jmpaddressc, jmpaddressz);

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
	localparam WAIT3  = 4'd10;
	localparam MEMLOAD= 4'd11;
	localparam READ   = 4'd12;
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
								case (opcode[6:4])
									3'h0	:	case (opcode[3:0])
										4'h1	:	state <= ECHO;	// OUTA
										4'h2	:	state <= READ;	// INA
										4'h3	:	begin flags <= 0; state <= FETCH;  end	// CLF
										default	:	state <= FETCH; // ignore all undefined 1 byte opcodes  NOTE!!! w.o. this default state stays DECODE and we have an issue then
												endcase
									3'h7	:	begin				// ALU 
													A <= result;
													flags[0] <= zero;
													flags[1] <= c_out;
													state <= FETCH;
												end
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
								7'h00	:	begin	// LDA immediate
												A <= operand;
												state <= FETCH;
											end
								7'h01	:	begin	// LDB immediate
												B <= operand;
												state <= FETCH;
											end
								7'h04	:	begin	// LDA <mem>
												c_raddr <= operand;
												state <= WAIT3;
											end
								7'h08	:	begin	// STA <mem> (no extra wait cycle because we can write and read at the same time)
												c_waddr <= operand;
												write_en <= 1;
												dwrite <= A;
												state <= FETCH;
											end
								7'h10	:	begin   // BRA <offset>
												pc <= jmpaddress;
												state <= FETCH;
											end
								7'h11	:	begin   // BRZ <offset>
												pc <= jmpaddressz;
												state <= FETCH;
											end
								default	:	state <= FETCH; // ignore all undefined 2 byte opcodes
							endcase
						end
			WAIT3	:	state <= MEMLOAD;
			MEMLOAD	:	begin
							A <= dread;
							state <= FETCH;
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
			READ	:	begin
							if (received) begin
								A <= rx_byte;
								state <= FETCH;
							end
						end
		endcase
	end

endmodule
