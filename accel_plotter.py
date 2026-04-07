import asyncio
import struct
import collections
import numpy as np
import matplotlib
import sys
import time

# 指定後端
try:
    matplotlib.use('TkAgg')
except:
    pass

import matplotlib.pyplot as plt
from bleak import BleakScanner, BleakClient

# Constants
UART_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
EXPECTED_PACKET_SIZE = 128
WINDOW_SIZE = 500 

class VBTPlotter:
    def __init__(self):
        self.data_x = collections.deque([0.0]*WINDOW_SIZE, maxlen=WINDOW_SIZE)
        self.data_y = collections.deque([0.0]*WINDOW_SIZE, maxlen=WINDOW_SIZE)
        self.data_z = collections.deque([0.0]*WINDOW_SIZE, maxlen=WINDOW_SIZE)
        self.rx_buffer = bytearray()
        self.new_data = False
        self.packet_count = 0
        
        plt.ion()
        self.fig, self.ax = plt.subplots(3, 1, figsize=(8, 6), sharex=True)
        self.line_x, = self.ax[0].plot([], [], 'r-', label='X')
        self.line_y, = self.ax[1].plot([], [], 'g-', label='Y')
        self.line_z, = self.ax[2].plot([], [], 'b-', label='Z')
        
        for i in range(3):
            self.ax[i].set_ylim(-16, 16)
            self.ax[i].grid(True)
            self.ax[i].legend(loc='upper right')
        
        self.ax[0].set_title("VBT Real-time Monitor (±16G)")
        plt.tight_layout()
        plt.show(block=False)

    def process_packet(self, sender, data):
        # 將收到的片段存入緩衝區
        self.rx_buffer.extend(data)
        
        # 只要緩衝區有完整的包，就持續解析
        while len(self.rx_buffer) >= EXPECTED_PACKET_SIZE:
            packet = self.rx_buffer[:EXPECTED_PACKET_SIZE]
            del self.rx_buffer[:EXPECTED_PACKET_SIZE]
            
            self.packet_count += 1
            scale = packet[120]
            if scale == 0: scale = 8
            
            # 解析數據
            raw_samples = struct.unpack(">60h", packet[0:120])
            for i in range(0, 60, 3):
                self.data_x.append((raw_samples[i] / 32768.0) * scale)
                self.data_y.append((raw_samples[i+1] / 32768.0) * scale)
                self.data_z.append((raw_samples[i+2] / 32768.0) * scale)
            
            self.new_data = True

    async def update_plot_loop(self):
        last_print = time.time()
        while True:
            if self.new_data:
                x_axis = np.arange(len(self.data_x))
                self.line_x.set_data(x_axis, list(self.data_x))
                self.line_y.set_data(x_axis, list(self.data_y))
                self.line_z.set_data(x_axis, list(self.data_z))
                
                for i in range(3):
                    self.ax[i].set_xlim(0, WINDOW_SIZE)
                
                self.fig.canvas.draw_idle()
                plt.pause(0.001)
                self.new_data = False
                
            if time.time() - last_print > 1.0:
                print(f"[Live] Packets: {self.packet_count} | Buf: {len(self.rx_buffer)} bytes", end='\r')
                last_print = time.time()
                
            await asyncio.sleep(0.01)

async def main():
    plotter = VBTPlotter()
    
    print("[Scanner] 正在搜尋 micro:bit [VBT_ULTRA]...")
    try:
        device = await BleakScanner.find_device_by_filter(
            lambda d, ad: d.name and "VBT" in d.name,
            timeout=10.0
        )
        
        if not device:
            print("[Error] 找不到設備。")
            return

        print(f"[Connect] 已連接至 {device.name} ({device.address})")
        async with BleakClient(device.address) as client:
            await client.start_notify(UART_RX_UUID, plotter.process_packet)
            print("[System] 數據包重新組裝功能已啟動，請觀察圖表...")
            await plotter.update_plot_loop()
                
    except Exception as e:
        print(f"\n[Error] {e}")
    finally:
        plt.close('all')
        print("\n[System] 程式結束。")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
