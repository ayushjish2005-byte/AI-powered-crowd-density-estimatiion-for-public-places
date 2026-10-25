import cv2
import numpy as np
from ultralytics import YOLO
import torch

WARNING_LIMIT = 10   # Yellow Alert Threshold (Moderate crowd)
CRITICAL_LIMIT = 15  # Red Alert Threshold (Overcrowded)

ENABLE_SERIAL = True
SERIAL_PORT = '/dev/cu.usbserial-0001' # macOS ESP32 Port
BAUD_RATE = 115200

ser = None

last_sent = None

def send_to_esp(count):
    global last_sent
    if ser is None:
        return
    if count >= CRITICAL_LIMIT:
        status = "CRIT"
    elif count >= WARNING_LIMIT:
        status = "WARN"
    else:
        status = "SAFE"
    msg = f"{status},{count}\n"
    if msg != last_sent:          # only send when something changes
        ser.write(msg.encode())
        last_sent = msg

if ENABLE_SERIAL:
    try:
        import serial
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to ESP32 on {SERIAL_PORT}")
    except Exception as e:
        print(f"Serial Connection Failed: {e}")

device = 'mps' if torch.backends.mps.is_available() else 'cpu'
print(f"Running M2 Acceleration on device: {device}")

model = YOLO('yolov8n.pt')

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

print("\n--- CONTROLS ---")
print("Press '+' or '=' to INCREASE Critical Limit")
print("Press '-' to DECREASE Critical Limit")
print("Press 'q' to QUIT\n")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Unmirror the webcam feed so left and right match the real scene.
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape
    density_map = np.zeros((h, w), dtype=np.float32)

    results = model(
        frame,
        stream=True,
        classes=[0],
        conf=0.50,
        iou=0.45,
        imgsz=1280,
        device=device,
        verbose=False,
    )

    person_count = 0
    for r in results:
        boxes = r.boxes
        for box in boxes:
            person_count += 1
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            cv2.circle(density_map, (cx, cy), 35, (1.0), -1)
            cv2.circle(density_map, (cx, cy), 35, (1.0), -1)

    send_to_esp(person_count)   # <-- new line (4 spaces, NOT 8 or 12)

    density_map = cv2.GaussianBlur(density_map, (71, 71), 0)
    density_map = cv2.GaussianBlur(density_map, (71, 71), 0)
    density_map = cv2.normalize(density_map, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    hotspot_color = np.full_like(frame, (40, 145, 230), dtype=np.uint8)
    hotspot_alpha = (density_map.astype(np.float32) / 255.0 * 0.30)[..., None]
    overlay = (
        frame.astype(np.float32) * (1.0 - hotspot_alpha)
        + hotspot_color.astype(np.float32) * hotspot_alpha
    ).astype(np.uint8)

    if person_count >= CRITICAL_LIMIT:
        status_text = "CRITICAL / OVERCROWDED"
        status_code = "2" # Code sent to ESP32
        theme_color = (0, 0, 255) # Red
    elif person_count >= WARNING_LIMIT:
        status_text = "WARNING / MODERATE"
        status_code = "1" # Code sent to ESP32
        theme_color = (0, 255, 255) # Yellow
    else:
        status_text = "SAFE / NORMAL"
        status_code = "0" # Code sent to ESP32
        theme_color = (0, 255, 0) # Green

    if ser and ser.is_open:
        payload = f"COUNT:{person_count};STATUS:{status_code}\n"
        ser.write(payload.encode('utf-8'))
        
    cv2.rectangle(overlay, (20, 20), (550, 130), (0, 0, 0), -1)
    cv2.rectangle(overlay, (20, 20), (550, 130), theme_color, 2)

    cv2.putText(overlay, f"People Count: {person_count}", (35, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    cv2.putText(overlay, f"Status: {status_text}", (35, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, theme_color, 2)
    cv2.putText(overlay, f"Critical Limit: {CRITICAL_LIMIT} (Use +/- keys)", (35, 118),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    fill_ratio = min(person_count / float(CRITICAL_LIMIT), 1.0)
    bar_width = int(510 * fill_ratio)
    cv2.rectangle(overlay, (25, 135), (535, 145), (50, 50, 50), -1)
    cv2.rectangle(overlay, (25, 135), (25 + bar_width, 145), theme_color, -1)

    cv2.imshow("M2 AI Crowd Density Estimator", overlay)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key in (ord('+'), ord('=')):
        CRITICAL_LIMIT += 5
        WARNING_LIMIT = int(CRITICAL_LIMIT * 0.7)
        print(f"Updated Limits -> Critical: {CRITICAL_LIMIT}, Warning: {WARNING_LIMIT}")
    elif key in (ord('-'), ord('_')):
        if CRITICAL_LIMIT > 5:
            CRITICAL_LIMIT -= 5
            WARNING_LIMIT = int(CRITICAL_LIMIT * 0.7)
            print(f"Updated Limits -> Critical: {CRITICAL_LIMIT}, Warning: {WARNING_LIMIT}")

if ser:
    ser.close()
cap.release()
cv2.destroyAllWindows()