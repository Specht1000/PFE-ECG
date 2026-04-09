# 🫀 PFE ECG — Portable Arrhythmia Detection System

## 📌 Overview
This project consists of the development of a **portable ECG monitoring system** capable of real-time signal acquisition, processing, and arrhythmia detection using embedded hardware and artificial intelligence.

The system is designed to be:
- Low-cost
- Portable
- Real-time capable
- Suitable for educational and prototyping purposes

---

## 🎯 Objectives

### General Objective
Develop an embedded system capable of acquiring ECG signals and detecting cardiac abnormalities in real time.

### Specific Objectives
- Acquire ECG signal using analog front-end (AD8232)
- Digitize signal using high-resolution ADC (ADS1115)
- Implement signal processing pipeline (Pan-Tompkins algorithm)
- Estimate heart rate (BPM)
- Detect R-peaks and anomalies
- Display results on OLED screen
- Integrate AI model for arrhythmia classification (offline/embedded)

---

## 🧠 System Architecture
![System Architecture](assets/SysArch.jpg)


---

## 🔧 Hardware Components

| Component | Description |
|----------|------------|
| ESP32-S3 | Main microcontroller (Wi-Fi + Bluetooth) |
| AD8232 | ECG analog front-end module |
| ADS1115 | 16-bit ADC (I2C interface) |
| OLED 1.3" | Display (SH1106, I2C) |
| Power supply | Power bank (5V USB) |
| Electrodes | ECG signal acquisition |

---

## 💻 Software Architecture

### Firmware (ESP-IDF)
- FreeRTOS-based multitasking
- Modular drivers:
  - `ecg_hw.c` → hardware interface  
  - `ads1115.c` → ADC communication  
  - `sh1106_oled.c` → display driver  
  - `ecg_processing.c` → signal processing  

### Tasks
- `taskApp` → ECG acquisition + processing + display  
- `taskMonitorTasks` → performance monitoring  

---

## 📊 Signal Processing

The system implements a simplified **Pan-Tompkins algorithm**, including:

- Bandpass filtering  
- Derivative stage  
- Squaring  
- Moving Window Integration  
- Adaptive thresholding  
- R-peak detection  

Outputs:
- Raw ECG signal  
- Filtered signal  
- Detected peaks  
- BPM estimation  

---

## 🤖 Artificial Intelligence (PC-side)

Training is performed using Python:

- Dataset preprocessing  
- Signal segmentation  
- Feature extraction  
- CNN-based classification (arrhythmias)  

📁 Location:
- src/
- models/
- notebooks/


⚠️ Note:  
Large datasets and processed arrays are not included in this repository.

---

## 📁 Project Structure
- PFE_ECG/
    - main/ # Firmware (ESP-IDF)
    - src/ # Python processing & AI
    - models/ # Trained models
    - scripts/ # Data processing scripts
    - notebooks/ # Experiments & analysis
    - reports/ # Documentation
    - data/ # (ignored if large)
    - platformio.ini
    - CMakeLists.txt
    - README.md


---

## ⚙️ How to Build (Firmware)

### Requirements
- PlatformIO  
- ESP-IDF  

### Build
```bash
pio run
```

### Flash
```bash
pio run -t upload
```

### Monitor
```bash
pio device monitor
```

## ⚡ Sampling
- Sampling rate: ~200 Hz
- Real-time processing on ESP32-S3

## 🔋 Power Supply
- Powered via USB (power bank)
- Low-power embedded operation

## 🚧 Current Status
- ✔ ECG acquisition
- ✔ Signal processing
- ✔ BPM estimation
- ✔ OLED visualization
- ✔ FreeRTOS integration
- 🔄 AI integration (in progress)

## 🔮 Future Improvements
- Embedded AI inference (TensorFlow Lite Micro)
- Mobile app integration (Bluetooth/Wi-Fi)
- Data logging (SD card / cloud)
- Noise reduction improvements
- Multi-lead ECG

## ⚠️ Disclaimer
- This project is for educational and research purposes only.
- It is not a medical device and must not be used for diagnosis.

## 👨‍💻 Author
- Guilherme Martins Specht
- Computer Engineering / Microelectronics
- PUCRS / Polytech Montpellier

## 📄 License
This project is open-source for academic use.
