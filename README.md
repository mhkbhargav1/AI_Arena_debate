# 🤖 AI Debate Arena

> An interactive web application where AI models debate topics in real time, built with Python and modern web technologies.

---

## 🚀 Features

- **Real-Time Debate Stream:** Watch AI models argue different sides of a topic dynamically.
- **Clean UI:** Responsive web interface built with custom HTML, CSS, and JavaScript.
- **Modular Backend:** Python application structure for API handling and orchestration.

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask or FastAPI)
- **Frontend:** HTML5, CSS3, JavaScript
- **Integrations:** LLM providers

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3
- Git
- API keys for any LLM providers used by the application

### 1. Clone the repository

```bash
git clone https://github.com/mhkbhargav1/AI_Arena_debate.git
cd AI_Arena_debate
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
```

On Windows:

```powershell
venv\Scripts\activate
```

On macOS/Linux:

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example environment file and add your API keys to `.env`:

```bash
cp .env.example .env
```

On Windows Command Prompt, use `copy .env.example .env` instead. Never commit your `.env` file or real API keys. Keep placeholder values in `.env.example` (for example, `OPENAI_KEY=your_key_here`).

### 5. Run the application

```bash
python app/main.py
```

These instructions assume the repository includes `requirements.txt`, `.env.example`, and `app/main.py`.

---

## 🗂️ Example Project Structure

```text
📦 AI_Arena_debate
 ┣ 📂 app
 ┃ ┣ 📂 static
 ┃ ┃ ┣ 📜 app.js
 ┃ ┃ ┣ 📜 index.html
 ┃ ┃ ┗ 📜 styles.css
 ┃ ┣ 📜 __init__.py
 ┃ ┗ 📜 main.py
 ┣ 📜 .env.example
 ┣ 📜 .gitignore
 ┣ 📜 README.md
 ┗ 📜 requirements.txt
```

The tree above is an example; adjust the setup commands if your project uses a different structure or entry point.

---

## 🧭 Repository Details

To update the repository's sidebar metadata, open the repository's main page on GitHub and click the gear icon next to **About**:

- **Description:** `Real-time multi-agent AI debate platform.`
- **Website:** Add a live demo link if the app is deployed.
- **Topics:** `ai`, `python`, `debate`, `llm`, `javascript`, `webapp`

Click **Save changes** when done.

---

## 🤝 Contributing

Contributions are welcome. Before opening a pull request, describe the change and include any relevant setup or testing steps. Please do not include API keys or other secrets in commits.

---

## 📄 License

Add a `LICENSE` file to the repository to make the project's reuse terms clear. For example, you can choose the MIT License if that matches your goals.
