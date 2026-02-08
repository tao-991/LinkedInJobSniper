import glob
import os
import smtplib
from typing import List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# web clawing imports if needed
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import random

import pandas as pd
from dotenv import load_dotenv
from jobspy import scrape_jobs

# LangChain Imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# read pdf
from pypdf import PdfReader



# Load environment variables
load_dotenv()

# Configuration
SEARCH_TERM = "Software Engineer (Python, Java)"
LOCATIONS = ["Tokyo, Japan", "Shanghai, China", "Hongkong, China"]
RESULT_LIMIT = 15
HOURS_OLD = 24
PROXY_URL = os.getenv("PROXY_URL", None)
RESUME = os.getenv("RESUME_TEXT", "")
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("API_BASE")
CRITERIA = os.getenv("CRITERIA", "")

# Define the output data structure from AI
class JobEvaluation(BaseModel):
    """
    Structure for job evaluation output.
    """

    score: int = Field(description="A relevance score from 0 to 100 based on the resume match and job preferences.")
    reason: str = Field(description="A concise, one-sentence reason for the score.")


# AI model
llm = ChatOpenAI(
    model_name="gemini-3-flash-preview",
    temperature=0,
    api_key=API_KEY,
    base_url=BASE_URL,
)


# structure output
structured_llm = llm.with_structured_output(JobEvaluation)

# system template
system_template = """
[Context]
You are an expert tech career coach. Your goal is to evaluate how well a job description matches a candidate's resume and preferences.

[Objectives]
Return a score by the following criteria and also give a concise, one-sentence reason for the score.

[Criteria]
1. Skill Match (50%): How well do the required skills and technologies in the job description align with those listed on the resume? (Programming Languages, Frameworks, Tools, etc,)
"""

system_template += CRITERIA


# Prompt template
prompt_template = ChatPromptTemplate.from_messages([
    ("system",
     system_template),
    ("user", """
    RESUME (Truncated):
    {resume}

    JOB TITLE: {title}
    JOB DESCRIPTION (Truncated):
    {description}

    Analyze the match. Be strict. If the tech stack is completely different, give a low score.
    """)
])


# Chain
evaluation_chain = prompt_template | structured_llm


# Read resume from Google Drive
def load_resume_from_google_drive() -> str:
    # retrive config
    creds_json_str = os.getenv("GCP_CREDENTIALS_JSON")
    file_id = os.getenv("RESUME_FILE_ID")

    if not creds_json_str or not file_id:
        print("❌  Google Drive credentials or file ID not provided.")
        return None

    print("🔐  Loading resume from Google Drive...")

    try:
        creds_dict = json.loads(creds_json_str)
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=["https://www.googleapis.com/auth/drive.readonly"])

        service = build('drive', 'v3', credentials=creds)

        requests = service.files().get_media(fileId=file_id)
        file_io = io.BytesIO()
        downloader = MediaIoBaseDownload(file_io, requests)

        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"   ⬇️  Downloading... {int(status.progress() * 100)}%")

        file_io.seek(0)
        reader = PdfReader(file_io)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"

        print("✅  Resume loaded successfully from Google Drive.")
        return text
    except Exception as e:
        print(f"❌  Failed to load resume from Google Drive: {e}")
        return None

if RESUME is None:
    RESUME = load_resume_from_google_drive()
    print(RESUME)

# web clawling functions
def fetch_missing_description(url: str, proxies: dict = None) -> str:
    """
    if the jobspy cannot fetch description, try to fetch from job url directly.
    -- For LinkedIn jobs only for now.
    """
    print(f"   ⛑️  Attempting manual fetch for: {url}...")

    # Set up headers
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
        "Accept-Language": "en-US,en;q=0.9",
        "Referrer": "https://www.google.com/"
    }

    try:
        # random sleep to mimic human behavior
        time.sleep(random.uniform(2, 5))

        # transfer the proxy to requests format (dictonary)
        proxies_dict = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

        response = requests.get(url, headers=headers, proxies=proxies, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            description_div = soup.find("div", {"class": "show-more-less-html__markup"}) or \
                              soup.find("div", {"class": "description__text"}) or \
                              soup.find("div", {"class": "job-description"})

            if description_div:
                text = description_div.get_text(separator="\n").strip()
                return text
            else:
                return soup.get_text()[:5000]
        else:
            print(f"     ❌  Failed to fetch page, status code: {response.status_code}")
            return ""
    except Exception as e:
        print(f"     ❌  Exception during manual fetch: {str(e)}")
        return ""

# scrape jobs
def get_jobs_data(location: str) -> pd.DataFrame:
    """
    Scrape job listings by JobSpy.

    Add Retry logic if needed.
    """
    proxies = [PROXY_URL] if PROXY_URL else None
    print(f"🕵️  CareerScout is searching for '{SEARCH_TERM}' in '{location}'...")
    print(f"🔌  Proxy: {proxies[0] if proxies else 'None'}")

    MAX_RETRIES = 5

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"   🔄 Attempt {attempt} of {MAX_RETRIES}...")
            jobs = scrape_jobs(
                site_name=["linkedin"],
                search_term=SEARCH_TERM,
                location=location,
                result_wanted=RESULT_LIMIT,
                hours_old=HOURS_OLD,
                proxies=proxies
            )

            print(f"✅  Scraped {len(jobs)} jobs.")
            return jobs
        except Exception as e:
            print(f"     ❌  Error on attempt {attempt}: {str(e)}")
            print(f"❌  Error during job scraping: {str(e)}")

            if attempt > MAX_RETRIES:
                wait_time = random.uniform(3, 6)
                print(f"   ⏳ Waiting for {wait_time:.2f} seconds before retrying...")
                time.sleep(wait_time)
            else:
                print("All retry attempts failed. Exiting scraping process.")
    return pd.DataFrame()


def evaluate_job(title: str, description: str) -> dict:
    """Using Langchain to evaluate a job posting against the resume."""
    if not description or len(str(description)) < 50:
        return {"score": 0, "reason": "Job description too short or missing"}

    try:
        # 调用 Chain
        result: JobEvaluation = evaluation_chain.invoke({
            "resume": RESUME[:3000],  # save token
            "title": title,
            "description": description[:3000]
        })
        return {"score": result.score, "reason": result.reason}

    except Exception as e:
        print(f"⚠️  AI Evaluation Error for '{title}': {e}")
        return {"score": 0, "reason": "AI Error"}

def send_email(top_jobs: List[dict]):
    if not top_jobs:
        print("📭  No matching jobs to send.")
        return

    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receiver = os.getenv("EMAIL_RECEIVER")

    subject = f"🚀 CareerScout: Top {len(top_jobs)} Jobs for {datetime.now().strftime('%Y-%m-%d')}"

    # HTML Email Template
    html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #2c3e50;">CareerScout Daily Report</h2>
            <p>Found <b>{len(top_jobs)}</b> high-match positions for you today:</p>
            <table style="border-collapse: collapse; width: 100%; max-width: 800px;">
                <tr style="background-color: #f8f9fa; text-align: left;">
                    <th style="padding: 10px; border-bottom: 2px solid #ddd;">Score</th>
                    <th style="padding: 10px; border-bottom: 2px solid #ddd;">Title</th>
                    <th style="padding: 10px; border-bottom: 2px solid #ddd;">Company</th>
                    <th style="padding: 10px; border-bottom: 2px solid #ddd;">Why Match?</th>
                    <th style="padding: 10px; border-bottom: 2px solid #ddd;">Action</th>
                </tr>
        """

    for job in top_jobs:
        color = "#27ae60" if job['score'] >= 85 else "#d35400"
        html_body += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: bold; color: {color};">
                        {job['score']}
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{job['title']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{job['company']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; font-size: 14px; color: #555;">
                        {job['reason']}
                    </td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">
                        <a href="{job['job_url']}" style="background-color: #007bff; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; font-size: 12px;">Apply</a>
                    </td>
                </tr>
            """

    html_body += """
            </table>
            <p style="margin-top: 20px; font-size: 12px; color: #888;">
                Powered by CareerScout-Agent using LangChain & Python.
            </p>
        </body>
        </html>
        """

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.send_message(msg)
        print(f"📧  Email sent successfully to {receiver}!")
    except Exception as e:
        print(f"❌  Email sending failed: {e}")


def main():
    # 1. Scraping
    df = pd.DataFrame()
    for location in LOCATIONS:
        df = pd.concat([df,get_jobs_data(location)], ignore_index=True, sort=False)
    if df.empty:
        return

    # # leave 3 jobs for testing
    # df = df.head(3)

    scored_jobs = []

    req_proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    # 2. Evaluation Loop
    print(f"🧠  Analyzing {len(df)} jobs with AI...")

    for _, row in df.iterrows():
        title = row.get('title', 'Unknown')
        description = row.get('description')
        job_url = row.get('job_url')

        if not description or len(str(description)) < 50:
            if job_url:
                description = fetch_missing_description(job_url, proxies=req_proxies)

        if not description or len(str(description)) < 50:
            print(f"   ⚠️  Skipping '{title}' due to insufficient description.")
            continue

        evaluation = evaluate_job(title, description)

        print()
        print(f"   📝 '{title}' scored {evaluation['score']}: {evaluation['reason']}")

        if evaluation['score'] >=50:  # 阈值过滤
            scored_jobs.append({
                "title": title,
                "company": row.get('company'),
                "job_url": row.get('job_url'),
                "score": evaluation['score'],
                "reason": evaluation['reason']
            })
        # 3. Sorting & Sending
        scored_jobs.sort(key=lambda x: x['score'], reverse=True)
        top_15 = scored_jobs[:15]

    send_email(top_15)

if __name__ == "__main__":
    main()