# micro:bit V2 High-Speed Accelerometer Streamer (VBT Pro)

這個專案專為 **高頻運動數據採集與 VBT (速度重量訓練) 分析** 設計，實現在 BBC micro:bit V2 上以 **1kHz (1000Hz)** 極速採樣，並透過手機 PWA 網頁進行即時分析與精確動作切分。

**🚀 立即使用：[VBT Pro Web App](https://chihhsiangchien.github.io/microbit-1kHz-accel-streamer)**

---

## 📖 快速開始 (一般使用者)

只需簡單兩步，即可開始 VBT 訓練分析：

### 第一步：燒錄韌體至 micro:bit
1.  從 **[Releases](https://github.com/ChihHsiangChien/microbit-1kHz-accel-streamer/releases/tag/v1.0)** 下載最新的 `MICROBIT.hex`。
2.  將 micro:bit 連接至電腦，將下載的檔案直接拖放（複製）到 micro:bit 磁碟機中。
3.  完成後，micro:bit 螢幕會滾動顯示您的裝置名稱（例如 `MB_vobuz`）。

### 第二步：開啟網頁並連線
1.  用手機或電腦瀏覽器開啟 **[VBT Pro Web App](https://chihhsiangchien.github.io/microbit-1kHz-accel-streamer)**。
2.  點擊「**連接 micro:bit**」，並在清單中選擇您的裝置名稱。
3.  **安裝 App (推薦)**：在手機 Chrome 點擊選單並選擇「**安裝應用程式**」，即可將 VBT Pro 加入桌面，像原生 App 一樣使用。

---

## 💡 功能指南

### 1. 重力校準 (Calibration)
在開始訓練前，將 micro:bit 固定在器材上並保持靜止，點擊「**重力校準**」。這能確保不論安裝角度如何，系統都能精確提取出垂直方向的加速度。校準值會自動儲存，下次開啟無需重複。

### 2. 雙軌分析工作流
*   **即時切分**：錄製完一組動作後，直接在圖表上縮放選取特定波峰，點擊「**分析當前範圍**」即可儲存為一次 Rep 紀錄。
*   **延後分析**：全力訓練時不分心操作，結束後點擊「**儲存原始資料**」。稍後可在歷史紀錄中點擊「**啟動分析器**」重新載入數據進行切分。

### 3. 切分技巧說明
*   **起始點**：框選範圍可以包含發力前的靜止段 (0G)。這有助於確保抓到完整的發力動作。
*   **安全性**：演算法已優化為僅計算「正向斜率 (RFD)」，因此即便框選到後段的下降/煞車區，也不會影響爆發力數據。

---

## 🛠️ 進階技術說明 (開發者與科學研究)

### 韌體實作原理 (main.cpp)
*   **1000Hz 穩定採樣**：透過底層 I2C (400kHz)、獨佔總線模式與精準計時，達成穩定 1ms 採樣間隔。
*   **硬體自動偵測**：支援 micro:bit v2.0 (LSM303) 與 v2.2 (QMA6100) 加速度計，自動套用優化暫存器設定。
*   **數據批次封裝**：每累積 20 筆數據 (120 Bytes) 封裝為一組 BLE 封包，大幅降低傳輸開銷。
*   **五點正向斜率法**：採用 Savitzky-Golay 導數濾波原理計算 RFD，具備極強的抗噪能力。

### Python 驗證工具
本專案提供 Python 工具用於數據流驗證與桌面端分析：
```bash
# 速率與數值測試 (驗證 1kHz 穩定度)
./venv/bin/python ble_speed_test.py
# 桌面端實時繪圖 (需 GUI 環境)
./venv/bin/python accel_plotter.py
```

### 資料格式 (128 Bytes BLE Packet)
| 偏移    | 長度 (Bytes) | 說明                                             |
| :------ | :----------- | :----------------------------------------------- |
| 0-119   | 120          | 20 個採樣點 (XYZ 三軸, 每軸 2 bytes, Big Endian) |
| 120     | 1            | 當前感測器量程 (G) (2, 4, 8, 16)                 |
| 121     | 1            | 感測器硬體地址 (50=LSM, 36=QMA)                  |
| 124-127 | 4            | 全局樣本索引 (用於計算丟包率)                    |

### 開發者環境設定 (Linux/Debian)
如果您需要修改源碼或自行編譯韌體：
```bash
# 安裝 ARM 工具鏈
sudo apt-get install -y gcc-arm-none-eabi binutils-arm-none-eabi libnewlib-arm-none-eabi
# 建立 Python 環境
python3 -m venv venv
./venv/bin/pip install bleak numpy scipy matplotlib
# 編譯韌體
python3 build.py -c
```

---
**Maintainer**: Chih-Hsiang Chien
**Project Home**: [GitHub Repository](https://github.com/ChihHsiangChien/microbit-1kHz-accel-streamer)
