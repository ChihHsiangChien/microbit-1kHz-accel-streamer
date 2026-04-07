import asyncio
import time
import struct
import collections
import numpy as np
from bleak import BleakScanner, BleakClient, BleakError

# Constants
UART_SERVICE_UUID = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
UART_RX_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
SAMPLES_PER_PACKET = 20
STATIONARY_WINDOW_MS = 500  # 500ms
STATIONARY_THRESHOLD = 0.05 # G variation threshold

class DataProcessor:
    def __init__(self):
        self.reset()

    def reset(self):
        self.last_index = None
        self.total_expected = 0
        self.total_lost = 0
        self.offsets = np.array([0.0, 0.0, 0.0])
        
        # Buffer for stationary detection
        self.window = collections.deque(maxlen=STATIONARY_WINDOW_MS)
        self.is_calibrating = False
        
        self.start_time = None
        self.packet_count = 0
        self.last_print = 0

    def process_packet(self, data):
        if len(data) != 128:
            return

        if self.start_time is None:
            self.start_time = time.time()
            self.last_print = self.start_time

        # 1. Extract Footer Info
        # [120] Scale, [124-127] Index
        scale = data[120]
        current_index = struct.unpack(">I", data[124:128])[0]
        
        # 2. Loss Detection & Interpolation
        if self.last_index is not None:
            gap = current_index - self.last_index - SAMPLES_PER_PACKET
            if gap > 0:
                self.total_lost += gap
                # Fill logic: for simplicity we'll just log it here, 
                # in a real app you'd append 'gap' items to your data stream.
                # print(f"[System] Lost {gap} samples at index {current_index}")
            self.total_expected += (gap + SAMPLES_PER_PACKET)
        else:
            self.total_expected += SAMPLES_PER_PACKET
        
        self.last_index = current_index
        self.packet_count += 1

        # 3. Parse 20 Samples efficiently
        # raw data is 20 * 6 = 120 bytes
        # Format: 20 sets of '>hhh' (Big Endian signed short X, Y, Z)
        raw_samples = struct.unpack(">60h", data[0:120])
        
        normalized_samples = []
        for i in range(0, 60, 3):
            # Scale conversion: raw / 32768 * scale_g
            # Note: micro:bit V2 LSM303AGR is left-aligned, handled by int16
            raw_xyz = np.array([raw_samples[i], raw_samples[i+1], raw_samples[i+2]])
            g_xyz = (raw_xyz / 32768.0) * scale
            
            # Apply dynamic offset
            calibrated_xyz = g_xyz - self.offsets
            normalized_samples.append(calibrated_xyz)
            self.window.append(calibrated_xyz)

        # 4. Dynamic Zero Calibration (Stationary Detection)
        if len(self.window) == STATIONARY_WINDOW_MS:
            samples_np = np.array(self.window)
            std_dev = np.std(samples_np, axis=0)
            
            # If standard deviation is very low, we assume device is stationary
            if np.all(std_dev < STATIONARY_THRESHOLD):
                # Update offset: Average of current window
                # We want X, Y to be 0, and Z to be 1G (or -1G depending on orientation)
                # For zero calibration, we usually target [0, 0, 0] or [0, 0, 1]
                # Here let's just stabilize around current mean for relative changes
                avg = np.mean(samples_np, axis=0)
                # Simple zeroing: shift X, Y to 0. For Z, we'd need to know orientation.
                # Let's just zero X and Y for this demo.
                self.offsets[0] = avg[0]
                self.offsets[1] = avg[1]
                # self.offsets[2] = avg[2] - 1.0 # Optional: calibrate Z to 1G

        # 5. Monitoring Output
        curr_time = time.time()
        if curr_time - self.last_print >= 1.0:
            elapsed = curr_time - self.start_time
            loss_rate = (self.total_lost / self.total_expected) * 100 if self.total_expected > 0 else 0
            sample_rate = (self.packet_count * SAMPLES_PER_PACKET) / elapsed
            
            # Get one sample for display
            latest = normalized_samples[-1]
            print(f"Scale: ±{scale}G | Rate: {sample_rate:.1f}Hz | Loss: {loss_rate:.2f}% | X:{latest[0]:.2f} Y:{latest[1]:.2f} Z:{latest[2]:.2f}")
            self.last_print = curr_time

async def run_client():
    processor = DataProcessor()
    
    while True:
        print("\n[Scanner] Searching for BBC micro:bit [MB_XXXXX]...")

        # 使用過濾器找尋符合的裝置
        device = await BleakScanner.find_device_by_filter(
                lambda d, ad: d.name and "MB_" in d.name,
                timeout=10.0
        )

        if not device:
            print("[Scanner] No device found. Retrying in 2s...")
            await asyncio.sleep(2.0)
            continue

        print(f"[Connect] Found {device.name} ({device.address}). Connecting...")
        
        try:
            async with BleakClient(device.address, timeout=15.0) as client:
                print(f"[BLE] Connected! MTU: {client.mtu_size}")
                processor.reset()
                
                # Nordic UART Service Handle
                await client.start_notify(UART_RX_UUID, lambda s, d: processor.process_packet(d))
                print("[System] Streaming started. Press Ctrl+C to stop.")
                
                # Keep alive until disconnect
                while client.is_connected:
                    await asyncio.sleep(1.0)
                    
        except BleakError as e:
            print(f"[Error] BLE Error: {e}")
        except asyncio.TimeoutError:
            print("[Error] Connection timed out.")
        except Exception as e:
            print(f"[Error] Unexpected error: {e}")
        
        print("[System] Disconnected or Failed. Re-entering scan mode in 3s...")
        await asyncio.sleep(3.0)

if __name__ == "__main__":
    try:
        asyncio.run(run_client())
    except KeyboardInterrupt:
        print("\n[System] Terminated by user.")
