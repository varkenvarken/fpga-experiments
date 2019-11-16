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
 */

`include "cores/osdvu/uart.v"
`include "ram.v"
`include "cpu.v"

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

	// uart wires
	wire u_reset = 0;
	wire [7:0] u_tx_byte;
	wire [7:0] u_rx_byte;
	wire u_transmit;
	wire u_received,u_is_receiving,u_is_transmitting;
	wire u_recv_error;

	// ram wires
	wire [7:0] r_din;
	wire [7:0] r_dout;
	wire r_write_en; 
	wire [8:0] r_waddr,r_raddr;

	// cpu wires
	wire c_reset, c_write_en, c_led, c_transmit, c_is_transmitting, c_halted;
	wire [7:0] c_dwrite, c_tx_byte;
	wire [8:0] c_raddr, c_waddr;

	// monitor wires and registers
	reg monitor_control = 1;

	// control address (for load/dump) and length
	reg [15:0] m_addr;
	reg [7:0] m_len;

	// access to uart
	reg [7:0] m_tx_byte;
	reg m_transmit;

	// access to ram
	reg [7:0] m_din;
	reg m_write_en;
	reg [8:0] m_waddr,m_raddr;

	// uart instantiation
	uart #(
		.baud_rate(9600),                 // The baud rate in kilobits/s
		.sys_clk_freq(12000000)           // The master clock frequency
	)
	uart0(
		.clk(iCE_CLK),                      // The master clock for this module
		.rst(u_reset),                      // Synchronous reset
		.rx(RS232_Rx_TTL),                  // Incoming serial line
		.tx(RS232_Tx_TTL),                  // Outgoing serial line
		.transmit(u_transmit),              // Signal to transmit
		.tx_byte(u_tx_byte),                // Byte to transmit
		.received(u_received),              // Indicated that a byte has been received
		.rx_byte(u_rx_byte),                // Byte received
		.is_receiving(u_is_receiving),      // Low when receive line is idle
		.is_transmitting(u_is_transmitting),// Low when transmit line is idle
		.recv_error(u_recv_error)           // Indicates error in receiving packet.
	);

	// ram instantiation
	ram ram0(
		.din(r_din), 
		.write_en(r_write_en), 
		.waddr(r_waddr), 
		.wclk(iCE_CLK), 
		.raddr(r_raddr), 
		.rclk(iCE_CLK), 
		.dout(r_dout)
	);

/*	// cpu instantiation
	cpu cpu0(
		.rst(c_reset),
		.clk(iCE_CLK),
		.dread(r_dout), // from ram to cpu
		.c_raddr(),
		.c_waddr(),
		.dwrite(c_dwrite), // from cpu to ram
		.write_en(c_write_en), 
		.led(c_led), 
		.tx_byte(c_tx_byte),
		.transmit(c_transmit),
		.is_transmitting(c_is_transmitting),
		.halted(c_halted)
	);
*/

	// interconnect wiring
	// led access comes from uart as well as cpu
	assign LED4 = u_recv_error;
	assign LED3 = c_led;

	// uart access is shared by monitor and cpu
	assign u_tx_byte = monitor_control ? m_tx_byte : c_tx_byte;
	assign u_transmit = monitor_control ? m_transmit : c_transmit;

	// ram access is shared by monitor and cpu
	assign r_waddr = monitor_control ? m_waddr : c_waddr;
	assign r_raddr = monitor_control ? m_raddr : c_raddr;
	assign r_write_en = monitor_control ? m_write_en : c_write_en;
	assign r_din = monitor_control ? m_din : c_dwrite;

	// monitor program state machine
	reg [2:0] m_state = 0;

	localparam START = 3'd0;
	localparam ADDR0 = 3'd1;
	localparam ADDR1 = 3'd2;
	localparam CHECK = 3'd3;
	localparam LOAD  = 3'd4;
	localparam LOAD1 = 3'd5;
	localparam DUMP  = 3'd6;
	localparam DUMP1 = 3'd7;

	localparam DOLOAD  = 2'd1;
	localparam DODUMP  = 2'd2;
	localparam DOEXEC  = 2'd3;

	always @(posedge iCE_CLK) begin
		m_transmit <= 0;
		m_write_en <= 0;
		c_reset <= 0;

		//if(c_halted) begin monitor_control <= 1; end

		case(m_state)
			START	:	if(u_received) begin m_addr[15:8] <= u_rx_byte; m_state <= ADDR0; m_tx_byte <= u_rx_byte; m_transmit <= 1; end
			ADDR0	:	if(u_received) begin m_addr[ 7:0] <= u_rx_byte; m_state <= ADDR1; m_tx_byte <= u_rx_byte; m_transmit <= 1; end
			ADDR1	:	if(u_received) begin m_len        <= u_rx_byte; m_state <= CHECK; m_tx_byte <= u_rx_byte; m_transmit <= 1; end
			CHECK	:	case(m_len[7:6])
							DOLOAD	:	begin m_len[7:6] <= 2'd0; m_state <= LOAD; end // e.g. h42 load 2 bytes
							DODUMP	:	begin m_len[7:6] <= 2'd0; m_state <= DUMP; end // e.g. h82 dump 2 bytes
							DOEXEC	:	begin c_reset <= 1; m_state <= START; monitor_control <= 0; end // e.g. hc0 start cpu
						endcase
			LOAD	:	if(u_received) begin
							if(m_len) begin
								m_waddr = m_addr[8:0];
								m_din = u_rx_byte;
								m_write_en = 1;
								m_len = m_len - 1;
								m_tx_byte = u_rx_byte;
								m_transmit <= 1;
								m_state <= LOAD1;
							end else
								m_state <= START;
						end
			LOAD1	:	begin
							m_addr[8:0] = m_addr[8:0] + 1;
							m_state <= m_len ? LOAD : START;
						end
			DUMP	:	if(m_len) begin
							m_len = m_len - 1;
							m_raddr = m_addr[8:0];
							m_state <= DUMP1;
						end else
							m_state <= START;
			DUMP1	:	if(!u_is_transmitting) begin
							m_addr[8:0] = m_addr[8:0] + 1;
							m_tx_byte = r_dout;
							m_transmit <= 1;
							m_state <= DUMP; // single wait cycle between transmits
						end
		endcase
		{LED2, LED1, LED0} <= m_state;
	end

endmodule
