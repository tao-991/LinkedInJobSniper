这是一份为你量身定制的 `README.md`。它不仅介绍项目功能，还详细写明了如何配置 GitHub Secrets（这是你项目运行的关键）。

你可以直接复制下面的内容，保存为项目根目录下的 `README.md` 文件。

---

# 🕵️‍♂️ LinkedIn Job Sniper

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-green.svg)
![LangChain](https://img.shields.io/badge/AI-LangChain-orange.svg)
![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)

**LinkedIn Job Sniper** is an automated AI agent that hunts for job opportunities on LinkedIn (and other platforms), evaluates them against your resume using LLMs (GPT-4o, DeepSeek, etc.), and sends you a daily summary of the top matches directly to your inbox.

Stop doom-scrolling LinkedIn. Let the AI agent work for you 24/7.

## ✨ Features

*   **🕵️ Automated Scraping**: Scrapes the latest jobs from LinkedIn using `python-jobspy` (with Proxy support to avoid bans).
*   **🧠 AI-Powered Analysis**: Uses LangChain and LLMs (OpenAI/DeepSeek) to semantically score jobs based on your actual resume, not just keywords.
*   **📧 Daily Email Digest**: Sends a beautifully formatted HTML email with the Top 10 matched jobs, including an AI-generated "Reason for Match".
*   **☁️ Zero Server Cost**: Runs entirely on **GitHub Actions** (Free Tier).
*   **🛡️ Robust & Resilient**: Built-in retry logic, proxy rotation, and error handling for stable operation.

## 🚀 How It Works

1.  **Trigger**: Runs automatically every day (via Cron) or manually via GitHub Actions.
2.  **Scrape**: Fetches job listings based on your search criteria (e.g., "Software Engineer" in "Singapore").
3.  **Evaluate**: The AI Agent reads your resume and creates a relevance score (0-100) and a reason for every job found.
4.  **Report**: Filters the best jobs and emails them to you.

## 🛠️ Configuration (GitHub Secrets)

To run this project, you need to configure **Repository Secrets** in your GitHub repository settings.

Go to: `Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`.

| Secret Name | Required | Description | Example Value |
| :--- | :---: | :--- | :--- |
| `API_KEY` | ✅ | Your LLM API Key (OpenAI or DeepSeek). | `sk-proj-123...` |
| `API_BASE` | ❌ | **Optional**. Custom Base URL for DeepSeek/OneAPI. | `https://api.deepseek.com/v1` |
| `EMAIL_SENDER` | ✅ | Your Gmail address. | `me@gmail.com` |
| `EMAIL_PASSWORD` | ✅ | Gmail **App Password** (Not login password). | `abcd efgh ijkl mnop` |
| `EMAIL_RECEIVER` | ✅ | Email address to receive the report. | `me@gmail.com` |
| `PROXY_URL` | ✅ | HTTP Proxy for scraping (Crucial for LinkedIn). | `http://user:pass@host:port` |
| `RESUME_CONTENT` | ✅ | Copy & Paste your entire resume text here. | `Name: Tao... Experience: ...` |
| `USER_NAME` | ❌ | Your name (for email footer watermark). | `Tao` |

> **⚠️ Note on Proxies**: LinkedIn has strict anti-bot measures. A high-quality **Residential Proxy** (e.g., IPRoyal, ThorData, Smartproxy) is highly recommended. Set the `PROXY_URL` format strictly as `http://user:pass@host:port`.

## 💻 Local Installation (For Development)

If you want to test it on your local machine:

1.  **Clone the repository**
    ```bash
    git clone https://github.com/tao-991/LinkedInJobSniper.git
    cd LinkedInJobSniper
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Setup Environment Variables**
    Create a `.env` file in the root directory:
    ```env
    OPENAI_API_KEY=sk-xxxx
    API_BASE=https://api.deepseek.com/v1  # Optional
    EMAIL_SENDER=me@gmail.com
    EMAIL_PASSWORD=xxxx
    EMAIL_RECEIVER=me@gmail.com
    PROXY_URL=http://user:pass@host:port
    RESUME_TEXT="Paste your resume text here or use resumes/ folder"
    ```

4.  **Add Resume (Optional)**
    Place your resume PDF in a folder named `resumes/` (e.g., `resumes/my_cv.pdf`). The script will prioritize the file over the environment variable.

5.  **Run**
    ```bash
    python main.py
    ```

## ⚙️ Customization

You can modify `main.py` to change search parameters:

```python
SEARCH_TERM = "Software Engineer"
LOCATION = "Singapore"
RESULTS_WANTED = 20  # Number of jobs to scrape per run
```

## ⚠️ Disclaimer

This tool is for educational purposes only. Web scraping may violate LinkedIn's User Agreement. Use this tool responsibly and at your own risk. The author is not responsible for any account bans or limitations.

---

### 👨‍💻 Author

**Tao**
*   Powered by Python, LangChain, and Coffee ☕.