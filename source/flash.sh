#!/bin/bash

# 設定正確的路徑
PROJECT_ROOT="$HOME/microbit-v2-samples"
BUILD_DIR="$PROJECT_ROOT/build"
HEX_FILE="$PROJECT_ROOT/MICROBIT.hex"   # 修改這裡：檔案在根目錄
MOUNT_POINT="$HOME/mnt/microbit"
DEVICE="/dev/sdb"

echo "🚀 開始編譯專案..."

# 1. 進入 build 目錄並執行編譯
cd $BUILD_DIR
make -j4

if [ $? -eq 0 ]; then
    echo "✅ 編譯成功！準備燒錄..."

    # 2. 檢查掛載點
    mkdir -p $MOUNT_POINT

    # 3. 掛載 (忽略已掛載的報錯)
    sudo mount $DEVICE $MOUNT_POINT 2>/dev/null

    # 4. 複製 hex 檔案 (直接從根目錄拿)
    echo "📥 正在從根目錄將 MICROBIT.hex 送入 Flash..."
    if [ -f "$HEX_FILE" ]; then
        sudo cp "$HEX_FILE" "$MOUNT_POINT/"
        
        # 5. 卸載 (確保數據完全寫入)
        sudo umount $MOUNT_POINT
        echo "🎉 燒錄完成！請觀察 micro:bit 燈號。"
    else
        echo "❌ 找不到 $HEX_FILE，請檢查編譯結果。"
    fi
    
    cd "$PROJECT_ROOT/source"
else
    echo "❌ 編譯失敗，請檢查程式碼錯誤。"
    cd "$PROJECT_ROOT/source"
    exit 1
fi
