/*
 * Copyright 2019 Michel Anders
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

`include "cores/osdvu/uart.v"

module top(
	input iCE_CLK,
	input RS232_Rx_TTL,
	output RS232_Tx_TTL,
	output LED0,
	output LED1,
	output LED2,
	output LED3,
	output LED4
	);

	wire reset = 0;
	reg transmit;
	reg [7:0] tx_byte;
	wire received;
	wire [7:0] rx_byte;
	wire is_receiving;
	wire is_transmitting;
	wire recv_error;

	wire [1:0] regno;
	wire [3:0] data_in;
	wire write;
	wire [3:0] data_out;

	assign LED4 = recv_error;

	uart #(
		.baud_rate(9600),                 // The baud rate in kilobits/s
		.sys_clk_freq(12000000)           // The master clock frequency
	)
	uart0(
		.clk(iCE_CLK),                    // The master clock for this module
		.rst(reset),                      // Synchronous reset
		.rx(RS232_Rx_TTL),                // Incoming serial line
		.tx(RS232_Tx_TTL),                // Outgoing serial line
		.transmit(transmit),              // Signal to transmit
		.tx_byte(tx_byte),                // Byte to transmit
		.received(received),              // Indicated that a byte has been received
		.rx_byte(rx_byte),                // Byte received
		.is_receiving(is_receiving),      // Low when receive line is idle
		.is_transmitting(is_transmitting),// Low when transmit line is idle
		.recv_error(recv_error)           // Indicates error in receiving packet.
	);

	reg [2:0] state = 0;
	reg [15:0] addr;
	reg [7:0] len;

	localparam START = 3'd0;
	localparam ADDR0 = 3'd1;
	localparam ADDR1 = 3'd2;
	localparam CHECK = 3'd3;
	localparam LOAD  = 3'd4;
	localparam DUMP  = 3'd5;
	localparam EXEC  = 3'd6;

	localparam DOLOAD  = 2'd1;
	localparam DODUMP  = 2'd2;
	localparam DOEXEC  = 2'd3;

	always @(posedge iCE_CLK) begin
		transmit <= 0;
		case(state)
			START	:	if(received) begin addr[15:8] <= rx_byte; state <= ADDR0; tx_byte <= rx_byte; transmit <= 1; end
			ADDR0	:	if(received) begin addr[ 7:0] <= rx_byte; state <= ADDR1; tx_byte <= rx_byte; transmit <= 1; end
			ADDR1	:	if(received) begin len        <= rx_byte; state <= CHECK; tx_byte <= rx_byte; transmit <= 1; end
			CHECK	:	case(len[7:6])
							DOLOAD	:	state <= LOAD; // e.g. h42 load 2 bytes
							DODUMP	:	state <= DUMP; // e.g. h82 dump 2 bytes
							DOEXEC	:	state <= EXEC; // e.g. hc0 jump
						endcase
			LOAD	:	if(received) state <= START;
			DUMP	:	if(received) state <= START;
			EXEC	:	if(received) state <= START;
		endcase
		{LED2, LED1, LED0} <= state;
	end
	
endmodule
