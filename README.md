# GovGPT Chatbot – Automated QA Test Suite

## 📌 Overview
This repository contains an end-to-end automated QA test suite for the **GovGPT AI-powered chatbot** launched by the UAE Government. The tests validate chatbot behavior, AI response quality, accessibility, language support, and UI consistency across desktop and mobile.

---

## 🛠 Installation Instructions 

### 1. Clone the Repository
```bash
git clone https://github.com/waqaskhalid3/uask-chatbot-qa.git
cd uask-chatbot-qa
```

### 2. Create & Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 💻 Recommended IDE
We recommend using **Visual Studio Code** for easy navigation, Git integration, and Python support.

- [Download VS Code](https://code.visualstudio.com/)
- Install Extensions:
  - Python
  - Pylance
  - GitLens

---

## 🌐 Configuring Test Language

To run the test cases for a specific language:

1. Open `data/test-data.json`
2. Locate the `"languages"` array under the `"ui_tests"` section:
   ```json
   "languages": ["en", "ar"]
   ```
   - To test only English, use: `["en"]`
   - To test only Arabic, use: `["ar"]`
   - To test both, use: `["en", "ar"]`

3. Save the file. The test suite will automatically pick up the selected languages.

---

## 🚀 How to Run Tests

### Run All Tests
```bash
pytest --html=test_report.html --self-contained-html
```

### Custom Parameters (if supported)
```bash
pytest -s tests/ --num-queries=5 --threshold=0.75
```

### Run a Specific Test File
```bash
pytest tests/test_ui_behavior.py
```

### Run a Specific Test Case
```bash
pytest -k "test_04_multilingual_support"
```

### Run in Headless Mode (Optional)
Edit `conftest.py` and add:
```python
options.add_argument("--headless")
```



---

## 🧪 List of Test Cases

### ✅ Chatbot UI Behavior
- Chat widget loads correctly on desktop and mobile
- User can send messages via input box
- AI responses are rendered properly
- Multilingual support (LTR for English, RTL for Arabic)
- Input is cleared after sending
- Scroll and accessibility
- Language toggle and field direction

### 🤖 GPT-Powered Response Validation
- Response accuracy and hallucination checks
- Format validation
- Loading and fallback state handling

### 🔐 Security Checks
- Script injection sanitization
- Malicious prompt handling

---

## 🗂 Project Structure

```
uask-chatbot-qa/
│
├── tests/
│   ├── test_01_ui_behavior.py
│   ├── test_02_security.py
│   └── test_03_response_validation.py
│
├── data/
│   ├── locators.json
│   └── test_data.json
│
├── utils/
│   └── helpers.py
│
├── screenshots/
│
├── logs/
│
├── conftest.py
├── requirements.txt
├── README.md
└── test_report.html
```

---

## 📄 Reports and Logs

### HTML Report
Auto-generated using:
```bash
pytest --html=test_report.html --self-contained-html
```

### Validation Logs
Stored in `logs/logs.log` for each run. Includes query, response, and pass/fail summary.

### Screenshots
On test failure, screenshots are saved in the `screenshots/` directory for debugging.

---

## 🤝 Contributing
Pull requests and suggestions are welcome!

---

## 🔒 License
This project is confidential and intended solely for internal QA review.
