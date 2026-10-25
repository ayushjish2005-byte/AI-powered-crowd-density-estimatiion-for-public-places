# AI-Powered Crowd Density Estimation for Public Spaces



An inexpensive, real-time crowd monitoring system that estimates crowd density from a live camera feed and triggers graded local physical alerts using an ESP32 microcontroller. Developed as an Engineering Clinic project at CGC University, Mohali.

---

## Features



* **Real-Time Detection:** Processes live video feeds using the lightweight pretrained YOLOv8n object-detection model restricted to the person class.


* **Density Heatmap:** Converts detections into a blurred density heatmap overlaid on the video feed to highlight high-density zones.


* **Threshold-Based Classification:** Evaluates crowd counts against adjustable **Safe**, **Warning**, and **Critical** thresholds, with runtime controls using the `+` and `-` keys.


* **Hardware Alert Unit:** Communicates status via a USB serial link (at 115200 baud) to an ESP32 microcontroller that drives a 16x2 I2C LCD, indicator LEDs, and an audible buzzer.



---

## System Architecture



1. **Software Pipeline (Python):** Captures 1280x720 video frames via OpenCV, runs YOLOv8n inference, calculates the person count, generates the heatmap, and sends status updates (`SAFE`, `WARN`, `CRIT`) only on state changes.


2. **Hardware Pipeline (ESP32):** Parses incoming serial messages to update the I2C LCD display, toggle the green/red status LEDs, and activate the 1 kHz buzzer during critical overcrowding.



---

## Hardware Requirements



| Component | Specification / Details

 |
| --- | --- |
| **Computer & Webcam** | Multi-core computer with webcam (Apple M2 laptop used; min. 8 GB RAM recommended)

 |
| **Microcontroller** | ESP32 Dev Module (Dual-core, GPIO, USB serial)

 |
| **Display** | 16x2 Character LCD with I2C backpack (Address: `0x27`)

 |
| **Indicators** | 1x Green LED, 1x Red LED (with current-limiting resistors)

 |
| **Audible Alert** | Buzzer (driven with a 1 kHz tone signal)

 |
| **Assembly** | Solderless breadboard, jumper wires, USB data cable

 |
 <img width="1086" height="1448" alt="Clean Electronics Prototype Setup" src="https://github.com/user-attachments/assets/b61fdf69-841f-4257-9a9f-3e0dd85485e2" />


---

## Software & Dependencies



* **Environment:** macOS, Visual Studio Code, Python 3.14.2, Arduino IDE 2.3.10


* **Python Libraries:** `ultralytics`, `opencv-python`, `numpy`, `torch`, `pyserial`


* **Model Weights:** `yolov8n.pt` (pretrained on the COCO dataset)


* **Arduino Libraries:** `Wire`, `LiquidCrystal_I2C`, and the ESP32 board package

<img width="1266" height="576" alt="image" src="https://github.com/user-attachments/assets/b9219cb6-6fdd-49c8-a327-eaa993444072" />


---

## Pin Configuration



| ESP32 Pin | Connected Component

 |
| --- | --- |
| **3V3 & GND** | LCD VCC/GND and breadboard ground rail

 |
| **GPIO 21** | LCD SDA line

 |
| **GPIO 22** | LCD SCL line

 |
| **GPIO 23** | Green LED (via resistor)

 |
| **GPIO 19** | Red LED (via resistor)

 |
| **GPIO 18** | Buzzer (positive terminal)

 |

---

## Usage & Controls



1. Flash the ESP32 firmware using the Arduino IDE with the correct serial port selected.


2. Run the main Python script in your environment.


3. Use the keyboard shortcuts during operation:
* **`+` / `-` keys:** Adjust the Critical and Warning threshold limits dynamically.


* **`q` key:** Quit the application.
