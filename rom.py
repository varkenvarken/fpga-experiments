template = """
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
    .INIT_0(256'h{init[0][0]:04x}{init[0][1]:04x}{init[0][2]:04x}{init[0][3]:04x}{init[0][4]:04x}{init[0][5]:04x}{init[0][6]:04x}{init[0][7]:04x}{init[0][8]:04x}{init[0][9]:04x}{init[0][10]:04x}{init[0][11]:04x}{init[0][12]:04x}{init[0][13]:04x}{init[0][14]:04x}{init[0][15]:04x}),
    .INIT_1(256'h{init[1][0]:04x}{init[1][1]:04x}{init[1][2]:04x}{init[1][3]:04x}{init[1][4]:04x}{init[1][5]:04x}{init[1][6]:04x}{init[1][7]:04x}{init[1][8]:04x}{init[1][9]:04x}{init[1][10]:04x}{init[1][11]:04x}{init[1][12]:04x}{init[1][13]:04x}{init[1][14]:04x}{init[1][15]:04x}),
    .INIT_2(256'h{init[2][0]:04x}{init[2][1]:04x}{init[2][2]:04x}{init[2][3]:04x}{init[2][4]:04x}{init[2][5]:04x}{init[2][6]:04x}{init[2][7]:04x}{init[2][8]:04x}{init[2][9]:04x}{init[2][10]:04x}{init[2][11]:04x}{init[2][12]:04x}{init[2][13]:04x}{init[2][14]:04x}{init[2][15]:04x}),
    .INIT_3(256'h{init[3][0]:04x}{init[3][1]:04x}{init[3][2]:04x}{init[3][3]:04x}{init[3][4]:04x}{init[3][5]:04x}{init[3][6]:04x}{init[3][7]:04x}{init[3][8]:04x}{init[3][9]:04x}{init[3][10]:04x}{init[3][11]:04x}{init[3][12]:04x}{init[3][13]:04x}{init[3][14]:04x}{init[3][15]:04x}),
    .INIT_4(256'h{init[4][0]:04x}{init[4][1]:04x}{init[4][2]:04x}{init[4][3]:04x}{init[4][4]:04x}{init[4][5]:04x}{init[4][6]:04x}{init[4][7]:04x}{init[4][8]:04x}{init[4][9]:04x}{init[4][10]:04x}{init[4][11]:04x}{init[4][12]:04x}{init[4][13]:04x}{init[4][14]:04x}{init[4][15]:04x}),
    .INIT_5(256'h{init[5][0]:04x}{init[5][1]:04x}{init[5][2]:04x}{init[5][3]:04x}{init[5][4]:04x}{init[5][5]:04x}{init[5][6]:04x}{init[5][7]:04x}{init[5][8]:04x}{init[5][9]:04x}{init[5][10]:04x}{init[5][11]:04x}{init[5][12]:04x}{init[5][13]:04x}{init[5][14]:04x}{init[5][15]:04x}),
    .INIT_6(256'h{init[6][0]:04x}{init[6][1]:04x}{init[6][2]:04x}{init[6][3]:04x}{init[6][4]:04x}{init[6][5]:04x}{init[6][6]:04x}{init[6][7]:04x}{init[6][8]:04x}{init[6][9]:04x}{init[6][10]:04x}{init[6][11]:04x}{init[6][12]:04x}{init[6][13]:04x}{init[6][14]:04x}{init[6][15]:04x}),
    .INIT_7(256'h{init[7][0]:04x}{init[7][1]:04x}{init[7][2]:04x}{init[7][3]:04x}{init[7][4]:04x}{init[7][5]:04x}{init[7][6]:04x}{init[7][7]:04x}{init[7][8]:04x}{init[7][9]:04x}{init[7][10]:04x}{init[7][11]:04x}{init[7][12]:04x}{init[7][13]:04x}{init[7][14]:04x}{init[7][15]:04x}),
    .INIT_8(256'h{init[8][0]:04x}{init[8][1]:04x}{init[8][2]:04x}{init[8][3]:04x}{init[8][4]:04x}{init[8][5]:04x}{init[8][6]:04x}{init[8][7]:04x}{init[8][8]:04x}{init[8][9]:04x}{init[8][10]:04x}{init[8][11]:04x}{init[8][12]:04x}{init[8][13]:04x}{init[8][14]:04x}{init[8][15]:04x}),
    .INIT_9(256'h{init[9][0]:04x}{init[9][1]:04x}{init[9][2]:04x}{init[9][3]:04x}{init[9][4]:04x}{init[9][5]:04x}{init[9][6]:04x}{init[9][7]:04x}{init[9][8]:04x}{init[9][9]:04x}{init[9][10]:04x}{init[9][11]:04x}{init[9][12]:04x}{init[9][13]:04x}{init[9][14]:04x}{init[9][15]:04x}),
    .INIT_A(256'h{init[10][0]:04x}{init[10][1]:04x}{init[10][2]:04x}{init[10][3]:04x}{init[10][4]:04x}{init[10][5]:04x}{init[10][6]:04x}{init[10][7]:04x}{init[10][8]:04x}{init[10][9]:04x}{init[10][10]:04x}{init[10][11]:04x}{init[10][12]:04x}{init[10][13]:04x}{init[10][14]:04x}{init[10][15]:04x}),
    .INIT_B(256'h{init[11][0]:04x}{init[11][1]:04x}{init[11][2]:04x}{init[11][3]:04x}{init[11][4]:04x}{init[11][5]:04x}{init[11][6]:04x}{init[11][7]:04x}{init[11][8]:04x}{init[11][9]:04x}{init[11][10]:04x}{init[11][11]:04x}{init[11][12]:04x}{init[11][13]:04x}{init[11][14]:04x}{init[11][15]:04x}),
    .INIT_C(256'h{init[12][0]:04x}{init[12][1]:04x}{init[12][2]:04x}{init[12][3]:04x}{init[12][4]:04x}{init[12][5]:04x}{init[12][6]:04x}{init[12][7]:04x}{init[12][8]:04x}{init[12][9]:04x}{init[12][10]:04x}{init[12][11]:04x}{init[12][12]:04x}{init[12][13]:04x}{init[12][14]:04x}{init[12][15]:04x}),
    .INIT_D(256'h{init[13][0]:04x}{init[13][1]:04x}{init[13][2]:04x}{init[13][3]:04x}{init[13][4]:04x}{init[13][5]:04x}{init[13][6]:04x}{init[13][7]:04x}{init[13][8]:04x}{init[13][9]:04x}{init[13][10]:04x}{init[13][11]:04x}{init[13][12]:04x}{init[13][13]:04x}{init[13][14]:04x}{init[13][15]:04x}),
    .INIT_E(256'h{init[14][0]:04x}{init[14][1]:04x}{init[14][2]:04x}{init[14][3]:04x}{init[14][4]:04x}{init[14][5]:04x}{init[14][6]:04x}{init[14][7]:04x}{init[14][8]:04x}{init[14][9]:04x}{init[14][10]:04x}{init[14][11]:04x}{init[14][12]:04x}{init[14][13]:04x}{init[14][14]:04x}{init[14][15]:04x}),
    .INIT_F(256'h{init[15][0]:04x}{init[15][1]:04x}{init[15][2]:04x}{init[15][3]:04x}{init[15][4]:04x}{init[15][5]:04x}{init[15][6]:04x}{init[15][7]:04x}{init[15][8]:04x}{init[15][9]:04x}{init[15][10]:04x}{init[15][11]:04x}{init[15][12]:04x}{init[15][13]:04x}{init[15][14]:04x}{init[15][15]:04x})
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

    assign rdata =  {{RDATA[14],RDATA[12],RDATA[10],RDATA[8],RDATA[6],RDATA[4],RDATA[2],RDATA[0]}};
	assign data = rdata[3:0];
	assign RADDR = {{7'b0, addr}};
	assign RCLK = clk;

endmodule
"""

# https://github.com/jamesbowman/swapforth/blob/master/j1a/mkrom.py
# https://stackoverflow.com/questions/41499494/how-can-i-use-ice40-4k-block-ram-in-512x8-read-mode-with-icestorm

def fanbits(byt):
    f = 0
    for i in range(8):
        if byt & (1 << i):
            f += 1 << i*2+1
    return f

def genrom(data):
    init = a=[[0] * 16 for i in range(16)]
    for i,d in enumerate(data):
        row = (i % 256) // 16
        col = 15 - i % 16
        bits= fanbits(d)
        bits= (bits >> 1) if i < 256 else bits
        init[row][col] |= bits
    
    return template.format(init = init)

data = "00 01 02 03 04 05 06 07 08 09 0a 0b 0c 0d 0e 0f";

data = [int(v, 16) for v in data.split()]

nbytes = len(data)

data = data + [0] * (512 - nbytes)

print(genrom(data))

