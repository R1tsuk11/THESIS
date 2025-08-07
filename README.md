# Arami: AI-Powered Waray Language Learning App

**Arami** is an educational app that helps users learn the Waray language through personalized and adaptive lessons. It integrates multiple AI components such as **Bayesian Knowledge Tracing (BKT)**, **Long Short-Term Memory (LSTM)** modeling, **Supermemo** for memory retention, and a **custom Waray speech recognition model** to provide accurate feedback and smart scheduling of lessons. Arami aims to promote regional language learning using modern and intelligent systems.

---

## Proponents

This project was developed as part of an undergraduate thesis for the Bachelor of Science in Computer Science Major in Software Engineering at FEU Institute of Technology.

**Team Members:**
- Miguelin III P. Arquiza (Speech Recognition Model Developer, Pronounciation Module Integration)
- Chelsea Anne E. Creer (Team Leader, Speech Data Collection, UI/UX, Documentation)
- Robert Gabriel M. Flores (Testing, Documentation, UI/UX)
- Benedict Adam T. Tumaning (Lead Developer, AI Models, Integration)

**Adviser:**
- Dr. Beau Gray M. Habal

## Features

- **Modular Lesson Design**  
  Structured lessons include vocabulary, sentence translation, and pronunciation practice.

- **Bayesian Knowledge Tracing (BKT)**  
  Tracks skill mastery and adjusts question difficulty based on real-time learner performance.

- **LSTM Learning Trends**  
  Monitors long-term learning patterns and predicts forgetting, feeding into personalized review schedules.

- **Waray Speech Recognition**  
  Provides pronunciation feedback using **phoneme matching** and **Dynamic Time Warping (DTW)** trained on Waray audio data.

- **SuperMemo 2** 
  For adaptive, spaced review scheduling to reinforce long-term memory.

- **Confidence Scoring System**  
  Enhances model feedback by evaluating the confidence of user responses and speech inputs.

- **Achievements & Progress Tracking**  
  Encourages engagement through badges and visual progress milestones.

- **Docker-Ready Deployment**  
  Easily run the app in any environment using Docker and Docker Compose.

---

## AI Components

| Component | Role |
|----------|------|
| **BKT** | Tracks vocabulary mastery and predicts when a user is ready to move on |
| **LSTM** | Models long-term behavior and memory decay for scheduling reviews |
| **Speech Model** | Waray `.keras` model with phoneme-level feedback |
| **Confidence Model** | Scores prediction reliability to refine BKT and LSTM updates |

---

## Tech Stack

- **Python 3.10+**
- **TensorFlow / Keras** – for the LSTM-based speech recognition model.
- **NumPy**, **Pandas** – for data processing and manipulation.
- **Dynamic Time Warping (DTW)** – for pronunciation similarity scoring.
- **SoundDevice**, **Librosa**, **Scikit-learn** – for audio processing and model evaluation.
- **Matplotlib** – for optional plotting and visualization.
- **Custom Implementation**:
  - Bayesian Knowledge Tracing (BKT)
  - SuperMemo 2 (Daily review algorithm)

---

### Requirements

```bash
# Recommended Python version
python==3.10.12

# Core libraries
numpy==1.24.4
pandas==2.0.3
scikit-learn==1.3.0
matplotlib==3.7.2

# Audio processing
librosa==0.10.1  
sounddevice==0.4.6  
soundfile>=0.10.3.post1  
pydub>=0.25.1  
SpeechRecognition>=3.8.1  
PyAudio  
fastdtw
ffmpeg #(https://ffmpeg.org/)  

# Deep learning
tensorflow==2.13.0
keras==2.13.1

# GUI
flet==0.27.6

# Database
pymongo==4.5.0

# Misc
python-dotenv==1.0.0  
seaborn>=0.11.2  

```

### Installation

### 1. Install Requirements

```bash
pip install -r requirements.txt
```

### 2. Clone Repository

```bash
git clone https://github.com/R1tsuk11/THESIS.git
