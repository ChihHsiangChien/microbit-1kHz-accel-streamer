# micro:bit V2 High-Speed Accelerometer Streamer (1kHz BLE)

這個專案專為 **高頻運動數據採集** 設計，實現在 BBC micro:bit V2 上以 **1kHz (1000Hz)** 極速採樣加速度計原始資料，並透過優化後的 BLE 串流技術將數據傳輸至電腦或手機進行即時分析。

## 核心特性

*   **1kHz 穩定採樣**：透過底層 I2C (400kHz)、獨佔總線模式與精準忙等計時，達成每秒 1000 次穩定採樣。
*   **硬體自動辨識 (Universal Support)**：自動適應 micro:bit V2.0 (使用 **LSM303AGR** 感測器) 與 V2.2 (使用 **QMA6100P** 感測器)。
*   **硬體唯一辨識**：藍牙名稱包含硬體獨特的 Friendly Name (例如 `MB_peget`)，開機時也會在螢幕顯示，方便辨識。
*   **高效能 Web App**：
    *   **零延遲繪圖**：數據採用 **原生 Canvas API** 手動渲染，徹底解決 1kHz 高頻數據導致的瀏覽器卡頓。
    *   **實時監控**：即時顯示 XYZ 三軸加速度數值與當前採樣頻率 (Hz)。
    *   **動態量程切換**：按下 **按鈕 A** 可循環切換 `±2G`, `±4G`, `±8G`, `±16G` 量程，Web App 會同步調整 Y 軸刻度。

## 快速開始

### 1. 韌體編譯與燒錄
```bash
# 確保已安裝 arm-none-eabi-gcc
python3 build.py -c
# 燒錄 (假設已掛載於 /media/pancala/MICROBIT)
cp MICROBIT.hex /media/pancala/MICROBIT/ && sync
```

### 2. 手機/電腦 Web App 使用
1.  開啟瀏覽器（建議 Chrome 或 Edge）。
2.  存取 [GitHub Pages 網址](https://ChihHsiangChien.github.io/microbit-1kHz-accel-streamer/) 或本地 `http://127.0.0.1:8000`。
3.  點擊「連接 micro:bit」，搜尋以 `MB_` 開頭的裝置。
4.  連線後即可看到實時三軸加速度圖表。

### 3. Python 驗證工具
```bash
# 速率與數值測試
./venv/bin/python ble_speed_test.py
# 桌面端實時繪圖 (需 GUI)
./venv/bin/python accel_plotter.py
```

## 開發者環境設定 (Linux/Debian/Raspberry Pi)

### 安裝工具鏈
```bash
sudo apt-get update
sudo apt-get install -y gcc-arm-none-eabi binutils-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib python3-tk
```

### 設定 Python 環境
```bash
python3 -m venv venv
./venv/bin/pip install bleak numpy scipy matplotlib opencv-python-headless
```

## 資料格式 (128 Bytes Packet)

| 偏移 | 長度 (Bytes) | 說明 |
| :--- | :--- | :--- |
| 0-119 | 120 | 20 個採樣點 (XYZ, 每個軸 2 bytes, Big Endian 補碼) |
| 120 | 1 | **當前量程 (G)** (2, 4, 8, 16) |
| 121 | 1 | **感測器 I2C 地址** (Debug: 50=LSM, 36=QMA) |
| 124-127 | 4 | **全局樣本索引** (用於計算丟包率) |

## 技術細節
*   **1kHz 穩定採樣**：透過底層 I2C (400kHz) 與精準忙等計時，達成每秒 1000 次穩定採樣。
*   **封裝發送策略**：硬體端並非每筆採樣都發送，而是累積 **20 筆採樣 (共 120 Bytes 數據)** 後，封裝成 128 Bytes 的大型封包一次發送。這大幅減少了 BLE 協定層的 Overhead，是達成 1kHz 串流的關鍵。
*   **FastUARTService**：自定義的藍牙服務，內部實作了 **環狀緩衝區 (Circular Buffer)**，並使用 **ASYNC (非同步)** 模式發送，確保數據傳輸不會阻塞 1kHz 的感測器讀取主迴圈。
*   **渲染機制**：Web App 端使用原生 Canvas API 隨數據流更新繪圖，最高支援每秒 50 次重繪 (對應每秒 50 個 128-byte 封包)，確保視覺流暢且不產生 UI 阻塞。
