`include "alu.v"

module cpu(
	input rst,
	input clk,
	input [7:0] dread, // from ram
	output reg [addr_width-1:0] c_raddr,
	output reg [addr_width-1:0] c_waddr,
	output reg [7:0] dwrite, // to ram
	output reg write_en,
	output reg led,
	output reg [7:0] tx_byte, 
	output reg transmit, 
	input is_transmitting,
	output reg halted,
	input [addr_width-1:0] startaddr,
	input received,
	input [7:0] rx_byte
	);
	parameter addr_width = 9;

	reg [addr_width-1:0] pc;
	reg [addr_width-1:0] sp; // stack pointer (could be reduced to 8 bits to save space); will be initialized to the last address
	reg [7:0] opcode, operand, outbyte;
	reg [7:0] A,B,C;
	reg [1:0] flags;
	wire [7:0] result;
	wire c_out, zero;
	wire [addr_width-1:0] jmpaddress, jmpaddressc, jmpaddressz;
	wire branchcondition;
	wire [3:0] alucode;
	wire [1:0] register;
	
	assign alucode = opcode[3:0];
	assign register= opcode[1:0];

	alu alu0(
		.a(A),
		.b(B),
		.carry(flags[1]),
		.op(alucode),
		.c(result),
		.carry_out(c_out),
		.zero(zero)
		);

	branchlogic #(.addr_width(addr_width)) branchlogic0(pc, operand, flags, jmpaddress, jmpaddressc, jmpaddressz);

	wire hlt = opcode == 8'h00;
	wire one = opcode[7] == 0;

	// state definitions
	localparam START     = 5'd0;
	localparam FETCH     = 5'd1;
	localparam DECODE    = 5'd2;
	localparam OPLOAD    = 5'd3;
	localparam ECHO      = 5'd4;
	localparam ECHO1     = 5'd5;
	localparam WAIT      = 5'd6;
	localparam WAIT2     = 5'd7;
	localparam OPLOAD2   = 5'd8;
	localparam DECODE2   = 5'd9;
	localparam WAIT3     = 5'd10;
	localparam MEMLOAD   = 5'd11;
	localparam READ      = 5'd12;
	localparam STACKPUSH = 5'd13;
	localparam STACKPUSH2= 5'd14;
	localparam CALL1     = 5'd15;
	localparam CALL2     = 5'd16;
	localparam CALL3     = 5'd17;
	localparam CALL4     = 5'd18;
	localparam CALL5     = 5'd19;
	localparam RETURN1   = 5'd20;
	localparam RETURN2   = 5'd21;
	localparam RETURN3   = 5'd22;
	localparam RETURN4   = 5'd23;
	localparam RETURN5   = 5'd24;
	reg [4:0] state = START;

	always @(posedge clk)
	begin
		led <= 0;
		write_en <= 0;
		transmit <= 0;
		halted <= 0;

		case(state)
			START	:	if(rst) begin 
							pc <= startaddr;
							sp <= {addr_width{1'b1}};
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
									3'h0	:	case (opcode[3:0])	// specials
										4'h1	:	state <= ECHO;	// OUTA
										4'h2	:	state <= READ;	// INA
										4'h3	:	begin flags <= 0; state <= FETCH;  end	// CLF
										default	:	state <= FETCH; // ignore all undefined 1 byte opcodes  NOTE!!! w.o. this default state stays DECODE and we have an issue then
												endcase
									3'h1	:	case (opcode[3:0])	// stack
										4'h8,
										4'h9	:	begin			// PUSHA, PUSHB
														c_waddr <= sp;
														write_en <= 1;
														dwrite <= register == 0 ? A : B;
														state <= STACKPUSH;
													end
										4'hc, 
										4'hd	:	begin			// POPA, POPB, plus room if we add C and/or D
														sp <= sp + 1;
														c_raddr <= sp + 1;
														state <= WAIT3;
													end
										4'h0	:	begin			// RET
														sp <= sp + 1;
														c_raddr <= sp + 1;
														state <= RETURN1;
													end
										default	:	state <= FETCH; // ignore all undefined 1 byte opcodes
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
							if (opcode[6:5] == 0) begin // regular opcodes
								case (opcode[4:0])
									5'h00	:	begin	// LDA immediate
													A <= operand;
													state <= FETCH;
												end
									5'h01	:	begin	// LDB immediate
													B <= operand;
													state <= FETCH;
												end
									5'h04,
									5'h05	:	begin	// LDA <mem> LDB <mem>
													c_raddr <= operand; // apparently automatically extended to width of c_raddr
													state <= WAIT3;
												end
									5'h08,
									5'h09	:	begin	// STA <mem> STB <mem> (no extra wait cycle because we can write and read at the same time)
													c_waddr <= operand;
													write_en <= 1;
													dwrite <= register == 0 ? A : B;
													state <= FETCH;
												end
									5'h10	:	begin   // BRA <offset>
													pc <= jmpaddress;
													state <= FETCH;
												end
									5'h11	:	begin   // BRZ <offset>
													pc <= jmpaddressz;
													state <= FETCH;
												end
									default	:	state <= FETCH; // ignore all undefined 2 byte opcodes
								endcase
							end else begin // long address opcodes
								case (opcode[6:5])
									2'h2	:	begin	// LDA <longmem>
													c_raddr <= {opcode[addr_width-8:0], operand};
													state <= WAIT3;
												end
									2'h1	:	begin	// STA <longmem>
													c_waddr <= {opcode[addr_width-8:0], operand};
													write_en <= 1;
													dwrite <= A;
													state <= FETCH;
												end
									2'h3	:	begin	// CALL <longmem>
														c_waddr <= sp;
														write_en <= 1;
														dwrite <= {{(16-addr_width){1'b0}},pc[addr_width-1:8]};
														state <= CALL1;
												end
									default	:	state <= FETCH; // ignore all undefined 2 byte longmem opcodes
								endcase
							end
						end
			WAIT3	:	state <= MEMLOAD;
			MEMLOAD	:	begin
							if (opcode[7:5] == 3'b110) begin // LDA <longmem>
								A <= dread; state <= FETCH;
							end else case (register)
								2'h0	: 	begin A <= dread; state <= FETCH; end
								2'h1	: 	begin B <= dread; state <= FETCH; end
								default		state <= FETCH; // ignore unknown register
							endcase
						end
			STACKPUSH:	state <= STACKPUSH2;
			STACKPUSH2:	begin
							sp <= sp - 1;
							state <= FETCH;
						end
			CALL1	:	state <= CALL2;
			CALL2	:	begin
							sp <= sp - 1;
							state <= CALL3;
						end 
			CALL3	:	state <= CALL4;
			CALL4	:	begin
							c_waddr <= sp;
							write_en <= 1;
							dwrite <= pc[7:0];
							state <= CALL5;
						end
			CALL5	:	begin
							sp <= sp - 1 ;
							pc <= {opcode[addr_width-8:0], operand};
							state <= FETCH;
						end
			RETURN1	:	state <= RETURN2;
			RETURN2	:	begin
							pc[7:0] <= dread;
							c_raddr <= sp + 1;
							sp <= sp + 1;
							state <= RETURN3;
						end
			RETURN3	:	state <= RETURN4;
			RETURN4	:	begin
							pc[addr_width-1:8] <= dread[addr_width-9:0];
							state <= RETURN5;
						end
			RETURN5	:	state <= FETCH;
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
