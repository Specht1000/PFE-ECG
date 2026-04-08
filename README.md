# PFE - ECG Arrhythmia Detection System

## 📌 Overview

This project aims to develop an embedded system for real-time ECG monitoring and arrhythmia detection.

The system combines:

- ECG signal acquisition
- Digital signal processing (Pan-Tompkins algorithm)
- Feature extraction (RR intervals, HR variability)
- Machine Learning classification

The embedded target is an ESP32, while training and validation are performed using real medical data from the MIT-BIH Arrhythmia Database.

---

## 🎯 Objectives

- Detect cardiac arrhythmias automatically
- Provide real-time alerts
- Validate results using a clinical dataset (MIT-BIH)
- Implement a lightweight model compatible with embedded systems

---

## 🧠 Project Architecture

The project is divided into two main parts:

### 1. Offline (PC - Python)

- Data loading (MIT-BIH)
- Signal preprocessing
- Feature extraction
- Model training
- Model validation

### 2. Embedded (ESP32)

- ECG acquisition (sensor)
- Signal filtering
- Feature extraction
- Real-time inference

---

## 📁 Project Structure
pfe_ecg/
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│ ├── raw/
│ │ └── mit_bih/
│ │ ├── 100.dat
│ │ ├── 100.hea
│ │ ├── 100.atr
│ │ └── ...
│ │
│ ├── interim/
│ │ ├── csv/
│ │ └── windows/
│ │
│ └── processed/
│ ├── features.csv
│ ├── train.csv
│ ├── test.csv
│ └── labels.csv
│
├── notebooks/
│ ├── 01_explore_mitbih.ipynb
│ ├── 02_feature_analysis.ipynb
│ └── 03_model_tests.ipynb
│
├── src/
│ ├── config.py
│ │
│ ├── dataset/
│ │ ├── read_mitbih.py
│ │ ├── convert_to_csv.py
│ │ └── split_dataset.py
│ │
│ ├── preprocessing/
│ │ ├── filters.py
│ │ ├── normalization.py
│ │ └── windowing.py
│ │
│ ├── features/
│ │ ├── rr_features.py
│ │ ├── time_domain.py
│ │ └── feature_builder.py
│ │
│ ├── models/
│ │ ├── train_sklearn.py
│ │ ├── train_mlp.py
│ │ ├── evaluate.py
│ │ └── predict.py
│ │
│ ├── export/
│ │ ├── save_model.py
│ │ ├── export_json.py
│ │ └── export_c_array.py
│ │
│ └── utils/
│ ├── io_utils.py
│ ├── plot_utils.py
│ └── metrics_utils.py
│
├── models/
│ ├── trained/
│ │ ├── model.pkl
│ │ └── scaler.pkl
│ │
│ └── exported/
│ ├── model.json
│ └── model.h
│
├── reports/
│ ├── figures/
│ ├── tables/
│ └── logs/
│
└── scripts/
├── run_pipeline.py
├── train_all.py
└── evaluate_model.py

---

## ⚙️ Workflow

### Step 1 — Data Preparation
- Load MIT-BIH dataset
- Convert signals to CSV format

### Step 2 — Preprocessing
- Apply filtering (noise removal)
- Normalize signals
- Segment into windows

### Step 3 — Feature Extraction
- RR intervals
- Heart rate
- Time-domain features

### Step 4 — Model Training
- Train classifiers (Random Forest, MLP)

### Step 5 — Evaluation
- Accuracy
- Confusion matrix
- Precision / Recall

### Step 6 — Export Model
- Convert model to embedded format (JSON or C array)

### Step 7 — Embedded Integration
- Implement inference on ESP32
- Real-time ECG analysis

---

## 🧪 Technologies Used

- Python
- NumPy
- Pandas
- Scikit-learn
- WFDB (MIT-BIH dataset)
- ESP-IDF (embedded system)

---

## 📊 Dataset

MIT-BIH Arrhythmia Database  
Source: PhysioNet

Contains annotated ECG recordings used for validation and training.

---

## 🚀 Future Improvements

- Implement full Pan-Tompkins algorithm on ESP32
- Use deep learning models (CNN)
- Mobile application integration
- MQTT communication for remote monitoring

---

## 👨‍💻 Author

Guilherme Martins Specht  
Computer Engineering / Embedded Systems  
Polytech Montpellier / PUCRS

---

## 📌 Notes

This project is part of a Final Year Project (PFE) and focuses on:

- Embedded systems
- Biomedical signal processing
- Artificial intelligence