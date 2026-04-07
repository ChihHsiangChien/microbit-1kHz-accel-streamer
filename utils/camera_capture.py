import cv2
import sys
import glob

def capture_image(filename="microbit_status.jpg"):
    # 尋找所有 /dev/video* 裝置
    devices = glob.glob("/dev/video*")
    if not devices:
        print("Error: No video devices found.")
        return False
    
    # 提取數字並排序，找到最大 index
    indices = [int(dev.replace('/dev/video', '')) for dev in devices]
    max_index = max(indices)
    
    print(f"Trying last camera index {max_index}...")
    cap = cv2.VideoCapture(max_index)
    
    # 如果最大的打不開，往前找
    if not cap.isOpened():
        print(f"Index {max_index} failed, trying {max_index - 1}...")
        cap = cv2.VideoCapture(max_index - 1)

    if cap.isOpened():
        # Wait for autofocus
        for _ in range(30):
            cap.read()
        ret, frame = cap.read()
        if ret:
            cv2.imwrite(filename, frame)
            print(f"Successfully captured image to {filename}")
            cap.release()
            return True
        cap.release()
        
    print("Error: Could not open the last cameras.")
    return False

if __name__ == "__main__":
    if capture_image():
        sys.exit(0)
    else:
        sys.exit(1)
