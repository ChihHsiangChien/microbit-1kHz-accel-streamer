# micro:bit V2 High-Speed Accelerometer Streamer (1kHz BLE)

這個專案專為 **高頻運動數據採集與 VBT (速度重量訓練) 分析** 設計，實現在 BBC micro:bit V2 上以 **1kHz (1000Hz)** 極速採樣加速度計原始資料，並透過優化後的 BLE 串流技術將數據傳輸至 PWA 網頁進行即時分析與精確動作切分。

## 核心特性 (v2.4.0)

*   **1kHz 穩定採樣**：透過底層 I2C (400kHz)、獨佔總線模式與精準計時，達成每秒 1000 次穩定採樣。
*   **VBT Pro 運動分析系統**：
    *   **重力投影校準**：自動計算重力矢量，無論 micro:bit 以何種角度安裝在槓鈴上，都能精確投影出純垂直加速度。
    *   **五點斜率法 (5-point Linear Regression)**：實作專業級 RFD (力發展率) 計算，具備強大的抗噪能力與精確性。
    *   **互動式錄製與切分**：支援長時錄製模式，並提供可縮放 (Zoom) 與平移 (Pan) 的互動圖表，讓使用者手動切分出特定動作區間進行分析。
    *   **數據持久化 (Local Storage)**：分析結果自動存入本機儲存空間，重整網頁或下次開啟時可隨時檢視歷史趨勢。
*   **PWA (Progressive Web App) 支援**：支援離線啟動，可直接安裝至 Android/iOS 手機桌面，提供接近原生 App 的操作體驗。
*   **零延遲即時繪圖**：數據採用 **原生 Canvas API** 手動渲染，徹底解決 1kHz 高頻數據導致的瀏覽器卡頓。
*   **動態量程切換**：按下 micro:bit **按鈕 A** 可循環切換 `±2G`, `±4G`, `±8G`, `±16G` 量程，App 會同步調整刻度。

## 快速開始

### 1. 韌體編譯與燒錄
```bash
# 確保已安裝 arm-none-eabi-gcc
python3 build.py -c
# 燒錄 (假設已掛載於 /media/pancala/MICROBIT)
cp MICROBIT.hex /media/pancala/MICROBIT/ && sync
```

### 2. 手機/電腦 Web App 使用
1.  開啟 Chrome 瀏覽器並存取專案網頁 (需 HTTPS 或 localhost)。
2.  點擊「連接 micro:bit」，搜尋以 `MB_` 開頭的裝置。
3.  **重力校準**：在開始前點擊「重力校準」以鎖定垂直軸。
4.  **錄製與切分**：切換至「錄製與切分」分頁進行一組訓練，結束後手動縮放圖表並點擊「分析目前範圍」來存檔。

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
*   **封裝發送策略**：硬體端累積 **20 筆採樣** 後封裝成 128 Bytes 封包發送，大幅減少 BLE Overhead。
*   **分析算法**：採用滑動窗口線性回歸計算當前斜率 (RFD)，有效過濾落地震動產生的尖峰雜訊。
*   **渲染機制**：Web App 端使用原生 Canvas API 隨數據流更新繪圖，確保視覺流暢且不產生 UI 阻塞。
