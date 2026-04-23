# DOCX to JSON

## Python Version
This repository uses **Python 3.12.8**. Tested on MacOS

## Setup Instructions

### 1. Create a Virtual Environment
```bash
python3 -m venv venv
```
### 2. Activate the Virtual Environment
```bash
source venv/bin/activate
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. This project uses OpenRouter for LLM inference.
Create a .env file in the root directory and add:
```bash
OPENROUTER_API_KEY=your_openrouter_api_key
```
### 6. How to run
```bash
python src/app.py input/sample.docx
```
**_NOTE:_**
- Ensure pip is up to date:
```bash
pip install --upgrade pip
```

- Deactivate the virtual environment when done:
```bash
deactivate
```

- Since Conda was activated by default, I deactivated it and used only the virtual environment:
```bash
conda deactivate
```
