`include "alu.v"
`include "rom.v"

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
	reg [addr_width-1:0] base0;
	reg [addr_width-1:0] base1;
	reg [addr_width-1:0] base1plusD;
	reg [7:0] opcode, operand; //, outbyte;
	reg [7:0] A,B,C,D;
	reg [1:0] flags;
	wire [7:0] result;
	wire c_out, zero;
	wire [addr_width-1:0] jmpaddress, jmpaddressc, jmpaddressz;
	wire branchcondition;
	wire [3:0] alucode;
	wire [1:0] register;
	wire [7:0] register_select;

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
	localparam START     = 5'd0; // next is START unless overruled
	localparam FETCH     = 5'd1; // next state is always WAIT
	localparam DECODE    = 5'd2; // next is FETCH unless overruled
	localparam OPLOAD    = 5'd3; // next state is always DECODE
	localparam ECHO      = 5'd4; // OBSOLETE next state is always ECHO1
	localparam ECHO1     = 5'd5; // next is ECHO1 unless overruled
	localparam WAIT      = 5'd6; // next state is always OPLOAD
	localparam WAIT2     = 5'd7; // next state is always OPLOAD2
	localparam OPLOAD2   = 5'd8; // next state is always DECODE2
	localparam DECODE2   = 5'd9; // next is FETCH unless overruled
	localparam WAIT3     = 5'd10; // next state is always MEMLOAD
	localparam MEMLOAD   = 5'd11; // next state is always FETCH
	localparam READ      = 5'd12; // next is READ unless overruled
	localparam STACKPUSH = 5'd13; // next state is always STACKPUSH2
	localparam STACKPUSH2= 5'd14; // next state is always FETCH
	localparam CALL1     = 5'd15; // next state is always CALL2
	localparam CALL2     = 5'd16; // next state is always CALL3
	localparam CALL3     = 5'd17; // next state is always CALL4
	localparam CALL4     = 5'd18; // next state is always CALL5
	localparam CALL5     = 5'd19; // next state is always FETCH
	localparam RETURN1   = 5'd20; // next state is always RETURN2
	localparam RETURN2   = 5'd21; // next state is always RETURN3
	localparam RETURN3   = 5'd22; // next state is always RETURN4
	localparam RETURN4   = 5'd23; // next state is always RETURN5
	localparam RETURN5   = 5'd24; // next state is always FETCH
	localparam WAITBASER = 5'd25; // next state is always WAITBASER1
	localparam WAITBASER1= 5'd26; // next state is always FETCH
	localparam STIDPWAIT = 5'd31; // next state is always FETCH
	reg [4:0] state = START;

	wire [4:0] rom_raddr, next_state;
	rom32x4 rom(rom_raddr, clk, next_state);
	assign rom_raddr = state;

	//reg [4:0] counter; // 5-bit counter that can be moved to A; not really enough for proper cycle counting

	always @(posedge clk)
	begin
		base1plusD <= base1 + D;
	end

	always @(posedge clk)
	begin
		write_en <= 0;
		transmit <= 0;
		halted <= 0;
		//counter <= counter + 1;
		if(state)	state <= next_state;  // this statement is crucial as apparently the first couple of cycles sbram can output anything ...
		case(state)
			START	:	if(rst) begin 
							pc <= startaddr;
							sp <= {addr_width{1'b1}};
							state <= FETCH;
						end
			FETCH	:	begin
							c_raddr <= pc; 
						end
			OPLOAD	:	begin
							opcode <= dread;
							pc <= pc + 1;
						end
			DECODE	:	begin
							c_raddr <= pc;
							if (hlt) begin // HLT
								state <= START;
								halted <= 1;
							end else if (one) begin // 1 byte opcode
								case (opcode[6:4])
									3'h0	:	case (opcode[3:0])	// specials
										4'h1	:	state <= ECHO;	// OUTA
										4'h2	:	state <= READ;	// INA
										4'h3	:	begin flags <= 0; state <= FETCH;  end	// CLF
										//4'hf	:	begin A <= {3'b0, counter}; state <= FETCH;  end
										default	:	state <= FETCH; // ignore all undefined 1 byte opcodes  NOTE!!! w.o. this default state stays DECODE and we have an issue then
												endcase
									3'h1	:	case (opcode[3:0])	// stack
										4'h8,
										4'h9,
										4'ha,
										4'hb	:	begin			// PUSHA, PUSHB, PUSHC, PUSHD
														c_waddr <= sp;
														write_en <= 1;
														case (register)
															2'b00	:	dwrite <= A;
															2'b01	:	dwrite <= B;
															2'b10	:	dwrite <= C;
															2'b11	:	dwrite <= D;
														endcase
														state <= STACKPUSH;
													end
										4'hc, 
										4'hd,
										4'he,
										4'hf	:	begin			// POPA, POPB, POPC, POPD
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
									3'h2	:	case(alucode)	// moves, only the ones that apply to the A register are implemented
													// note that including all the commented out stuff and removing the default to create a full case actual increases LC count with 25
													//4'b0000,  // begin A <= A; state <= FETCH; end
													4'b0100	: begin A <= B; state <= FETCH; end
													4'b1000	: begin A <= C; state <= FETCH; end
													4'b1100	: begin A <= D; state <= FETCH; end
													4'b0001	: begin B <= A; state <= FETCH; end
													//4'b0101,  //begin B <= B; state <= FETCH; end
													//4'b1001,  //begin B <= C; state <= FETCH; end
													//4'b1101,  //begin B <= D; state <= FETCH; end
													4'b0010	: begin C <= A; state <= FETCH; end
													//4'b0110,  // begin C <= B; state <= FETCH; end
													//4'b1010,  // begin C <= C; state <= FETCH; end
													//4'b1110,  // begin C <= D; state <= FETCH; end
													//4'b0111,  // begin D <= B; state <= FETCH; end
													//4'b1011,  // begin D <= C; state <= FETCH; end
													//4'b1111,  // begin D <= D; state <= FETCH; end
													4'b0011	: begin D <= A; state <= FETCH; end
													default : state <= FETCH;
												endcase
									3'h3	:	case(alucode)	// base register LD/ST
													4'b0000,
													4'b0010	: begin // LDA (base0 + C)
																c_raddr <= base0 + C;
																state <= WAITBASER;
															  end
													4'b1001,
													4'b1011	: begin // STA (base1 + D)
																c_waddr <= base1plusD;
																write_en <= 1;
																dwrite <= A;
																state <= FETCH; // STIDPWAIT;
																//if(register==3)	D <= D + 1;
															  end
													default : state <= FETCH;
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
			WAIT2	:	state <= next_state;
			OPLOAD2	:	begin
							operand <= dread;
							pc <= pc + 1;
						end
			DECODE2	:	begin
							case (opcode[6:5]) 
								0: case (opcode[4:0])
									5'h00	:	begin	// LDA immediate
													A <= operand;
													state <= FETCH;
												end
									5'h01	:	begin	// LDB immediate
													B <= operand;
													state <= FETCH;
												end
									5'h02	:	begin	// LDC immediate
													C <= operand;
													state <= FETCH;
												end
									5'h03	:	begin	// LDD immediate
													D <= operand;
													state <= FETCH;
												end
									5'h04,
									5'h05,
									5'h06,
									5'h07	:	begin	// LDA <mem> LDB <mem>
													c_raddr <= operand; // apparently automatically extended to width of c_raddr
													state <= WAIT3;
												end
									5'h08,
									5'h09,
									5'h0a,
									5'h0b	:	begin	// STA <mem> STB <mem> (no extra wait cycle because we can write and read at the same time)
													c_waddr <= operand;
													write_en <= 1;
													dwrite <= register == 0 ? A : ( register == 1 ? B : (register == 2 ? C : D));
													state <= FETCH;
												end
									5'h0c,
									5'h0d,
									5'h0e,
									5'h0f,
									5'h13,
									5'h14,
									5'h15,
									5'h16,
									5'h17,
									5'h18,
									5'h19,
									5'h1a,
									5'h1b,
									5'h10	:	begin   // BRA <offset>
													pc <= jmpaddress;
													state <= FETCH;
												end
									5'h11	:	begin   // BRZ <offset>
													pc <= jmpaddressz;
													state <= FETCH;
												end
									5'h12	:	begin   // BRC <offset>
													pc <= jmpaddressc;
													state <= FETCH;
												end
									5'h1c,
									5'h1d,
									5'h1e,
									5'h1f	:	begin  // LDAS, LDBS, LDCS, LDDS
													c_raddr <= sp + operand;
													state <= WAIT3;
												end
									5'h14,
									5'h15,
									5'h16,
									5'h17	:	begin	// STAS STBS STCS STDS
													c_waddr <= sp + operand;
													write_en <= 1;
													dwrite <= register == 0 ? A : ( register == 1 ? B : (register == 2 ? C : D));
													state <= FETCH;
												end
									//default	:	state <= FETCH; // ignore all undefined 2 byte opcodes
								   endcase
								1: begin	// LDBASE0
										base0 <= {opcode[addr_width-8:0], operand};
										state <= FETCH;
								   end
								2	:	begin	// LDBASE1
											base1 <= {opcode[addr_width-8:0], operand};
											state <= FETCH;
										end
								3	:	begin	// CALL <longmem>
											c_waddr <= sp;
											write_en <= 1;
											dwrite <= {{(16-addr_width){1'b0}},pc[addr_width-1:8]};
											state <= CALL1;
										end
								//	default	:	state <= FETCH; // ignore all undefined 2 byte longmem opcodes
							endcase
						end
			MEMLOAD	:	begin
							case (register)
								2'h0	: 	begin A <= dread; end
								2'h1	: 	begin B <= dread; end
								2'h2	: 	begin C <= dread; end
								2'h3	: 	begin D <= dread; end
							endcase
						end
			//WAITBASER:	if(register == 2)	C <= C + 1;
			WAITBASER1:	begin 
							A <= dread;
							if(register == 2)	C <= C + 1;
						end
			STACKPUSH2:	begin
							sp <= sp - 1;
						end
			CALL2	:	begin
							sp <= sp - 1;
						end 
			CALL4	:	begin
							c_waddr <= sp;
							write_en <= 1;
							dwrite <= pc[7:0];
						end
			CALL5	:	begin
							sp <= sp - 1 ;
							pc <= {opcode[addr_width-8:0], operand};
						end
			RETURN2	:	begin
							pc[7:0] <= dread;
							c_raddr <= sp + 1;
							sp <= sp + 1;
							state <= next_state;  // eliminating this line *increases* LC count
						end
			RETURN4	:	begin
							pc[addr_width-1:8] <= dread[addr_width-9:0];
						end
			//ECHO	:	begin
			//				outbyte <= A;
			//			end
			ECHO1	:	begin
							if(!is_transmitting) begin
								tx_byte <= A;
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
			STIDPWAIT:	begin
							write_en <= 1;
							//if(register==3)	D <= D + 1;
						end
		endcase
	end

endmodule
