# 📬 Email Automation System + Monitoring Dashboard
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Last Commit](https://img.shields.io/github/last-commit/patla001/email-automation-dashboard)

This project is a fully functional, AI-powered email classification and response automation system with a real-time **Streamlit dashboard** for monitoring metrics and delivery performance.

It integrates:
- 🤖 **OpenAI GPT** to intelligently classify and respond to emails
- 📤 **Mailtrap SMTP** to send real emails in a safe test environment
- 🎟️ **Zendesk API** to create real support and feedback tickets when automated handling fails or is escalated
- 📊 **Streamlit** to visualize system performance, errors, and trends

---

## 🚀 Features

- 📥 Classifies incoming emails into: `complaint`, `inquiry`, `feedback`, `support_request`, or `other`
- 🧠 Uses **zero-shot prompting** with OpenAI to improve classification and generate relevant, context-sensitive responses
- ✉️ Generates automated responses without requiring labeled training data
- ✅ Sends **real emails** using [Mailtrap](https://mailtrap.io/) (safe for testing)
- 🛠️ Creates **real tickets** in [Zendesk](https://www.zendesk.com/) for support and feedback escalation
- 🗃 Logs every response and error to a local JSON file
- 📈 Provides a live dashboard with:
  - Total processed emails
  - Error and success rates
  - Classification breakdown (charts)
  - Filtering and CSV export
- Trigger AI classification with sample email inputs
- Show SMTP failure → Zendesk ticket creation fallback
- Navigate dashboard to explain error tracking and resolution
---

## 📦 Installation

Install required libraries:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the main app

```bash
python main.py
```

---
## ▶️ Running the test cases

```bash
python testcases.py
```

---

## ▶️ Running the Dashboard

```bash
streamlit run dashboard.py
```

---

## Design Decision

![Alt Text](https://github.com/patla001/email-automation-dashboard/blob/main/CadreAI-architecture-diagram.gif)

---

## 🔐 Environment Variables

Set the following variables in a `.env` file:

```env
OPENAI_API_KEY=your-openai-api-key

# Mailtrap SMTP (used to send real emails in test)
EMAIL_USER=your-mailtrap-username
EMAIL_PASS=your-mailtrap-password

# Zendesk (used to create real support/feedback tickets)
ZENDESK_DOMAIN=https://your-subdomain.zendesk.com
API_TOKEN=your-zendesk-api-token
API_USER=your-zendesk-email/token
```

---

## 📁 Project Structure

```
├── dashboard.py                    # Streamlit dashboard UI
├── main.py                         # Main application
├── testcases.py                    # Test Cases or Edge Cases
├── emailProcessor.py               # Log of sent and failed responses
├── processFunc.py                  # Zero-shot prompting function
├── emailAutomationSystem.py        # Email Automation Class
├── email_automation_service.py     # Mailtrap and Zendesk API Services
├── sent_responses_log.json         # Log of sent and failed responses
├── requirements.txt                # Python Libraries Requirements
├── .env.example                    # Sample env file
└── README.md
```

---

## 📊 Dashboard Insights

- Overview of success/error rates
- Interactive charts showing classification trends
- Filtering by category/status
- Downloadable CSV logs
- Real-time refresh support

> Powered by **Streamlit**, **Altair**, **Pandas**, and integrated with **Mailtrap** and **Zendesk** APIs.

---

## 🤖 Prompting Strategy (Zero-Shot with GPT)

This system uses **zero-shot prompting** with OpenAI GPT to classify and respond to emails without any prior training or labeled data. Instead of relying on pre-trained task-specific models, the system dynamically builds prompts that describe the task clearly in plain language and lets the LLM infer the correct classification or response.

### 📌 Example: Classification Prompt

```text
You are an email classifier. Read the email and respond with the appropriate category as JSON:
- complaint
- inquiry
- feedback
- support_request
- other

Respond only in this format:
{
  "classification": "complaint"
}

Email:
Subject: Delayed Shipment
Body: I've been waiting for my order for over two weeks and I’m getting frustrated.
```

### ✅ Why Zero-Shot?
- No labeled dataset needed
- Easy to adjust logic via prompt
- Adapts to edge cases and real-world phrasing
- Consistent, explainable outputs

### ✉️ Response Prompting
The system uses similarly structured zero-shot prompts to ask the model to write context-sensitive, category-aware email responses using the original message.

> This approach allows for rapid deployment and adaptability across a wide range of user inputs, with minimal fine-tuning or manual rule-writing.

---

## 📬 Contact

Created by Ezer Patlan  

