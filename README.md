# micro:bit V2 High-Speed VBT Motion Tracker (1kHz BLE)

這個專案專為 **VBT (Velocity Based Training)** 設計，實現在 BBC micro:bit V2 上以 **1kHz (1000Hz)** 極速採樣加速度計原始資料，並透過優化後的 BLE 串流技術將數據傳輸至電腦進行即時分析。

## 核心特性

*   **1kHz 穩定採樣**：透過底層 I2C (400kHz)、獨佔總線模式與精準忙等計時，達成每秒 1000 次穩定採樣。
*   **硬體自動辨識 (Universal Support)**：自動適應 micro:bit V2.0 (使用 **LSM303AGR** 感測器) 與 V2.2 (使用 **QMA6100P** 感測器)。
*   **動態量程切換**：按下 **按鈕 A** 可循環切換 `±2G`, `±4G`, `±8G`, `±16G` 量程。
*   **視覺狀態反饋**：
    *   **量程顯示**：LED 矩陣第一排點亮的數量表示當前量程 (1燈=2G, 4燈=16G)。
    *   **系統心跳**：LED 矩陣最後一排的小點會持續左右跳動，確認系統採樣正常執行。
*   **高效 BLE 串流 (FastUART)**：
    *   封包聚合：每 20 個樣本封裝為一個 128-byte 數據包。
    *   數據包重組邏輯：Python 接收端具備自動 Reassembly 功能，能處理 BLE MTU 限制導致的分段數據。

## 開發者環境設定 (Linux/Debian/Raspberry Pi)

### 1. 安裝 ARM 交叉編譯工具鏈
```bash
sudo apt-get update
sudo apt-get install -y gcc-arm-none-eabi binutils-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib python3-tk
```

### 2. 設定 Python 虛擬環境與依賴
專案提供完整的運動數據處理與繪圖環境：
```bash
rm -rf venv
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install bleak numpy scipy matplotlib opencv-python-headless
```

## 快速開始

### 1. 編譯與燒錄
```bash
# 編譯
python3 build.py -c
# 燒錄 (假設已掛載於 /media/pancala/MICROBIT)
cp MICROBIT.hex /media/pancala/MICROBIT/ && sync
```

### 2. 數據接收與驗證
```bash
# 基礎速率與數值測試
./venv/bin/python ble_speed_test.py

# 即時波形繪圖 (需 GUI 環境)
./venv/bin/python vbt_plotter.py
```

## 資料格式 (128 Bytes Packet)

| 偏移 | 長度 (Bytes) | 說明 |
| :--- | :--- | :--- |
| 0-119 | 120 | 20 個採樣點 (XYZ, 每個軸 2 bytes, Big Endian 補碼) |
| 120 | 1 | **當前量程 (G)** (2, 4, 8, 16) |
| 121 | 1 | **偵測到的感測器 I2C 地址** (Debug 用) |
| 122-123 | 2 | 保留位元 (Padding) |
| 124-127 | 4 | **全局樣本索引** (Big Endian, 用於丟包計算) |

## 技術細節
*   **裝置名稱**：`BBC micro:bit [VBT_ULTRA]`
*   **採樣頻率**：~1000 Hz
*   **連線間隔**：7.5ms - 15ms
*   **數據包組裝**：Python 端使用 `bytearray` 緩衝區確保在任何 MTU 設定下都能正確解析 128-byte 數據包。
