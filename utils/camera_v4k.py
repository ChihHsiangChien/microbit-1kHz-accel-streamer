import cv2
import sys

def capture_v4k(filename="microbit_v4k.jpg"):
    print("Attempting to open IPEVO V4K on /dev/video0...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open /dev/video0. It might be busy.")
        return False
    
    # Try to set resolution to something common for V4K
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Wait for sensor to warm up and auto-adjust
    for _ in range(40):
        cap.read()
        
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(filename, frame)
        print(f"Successfully captured image from V4K to {filename}")
    else:
        print("Error: Opened V4K but could not read frame.")
    
    cap.release()
    return ret

if __name__ == "__main__":
    if capture_v4k():
        sys.exit(0)
    else:
        sys.exit(1)
