# AgriLens AI 🌱

**AI Vision • Agriculture**

AgriLens AI is a Streamlit vision-powered agriculture chatbot. A user uploads a plant, leaf, fruit, stem, or crop image, chats with Gemini about visible symptoms, generates a concise conversation summary, and can send that summary through **WhatsApp or SMS** using Twilio.

## ✨ What it does

1. 📸 Upload a clear plant/crop image.
2. 🔍 Gemini analyzes visible symptoms and gives a possible issue category with uncertainty.
3. 💬 Continue asking questions about the same image.
4. 📝 Generate a concise summary of the conversation.
5. 📱 Send the summary by WhatsApp or SMS.
6. 🔄 Start a new analysis whenever needed.

The app intentionally presents image-based observations as **possible issues**, not guaranteed diagnoses.

## 🧱 Tech stack

- **Frontend:** Streamlit
- **Vision + conversation:** Google Gemini API (`gemini-3.8-flash`)
- **Messaging:** Twilio Programmable Messaging
- **Deployment:** Streamlit Community Cloud
- **Language:** Python

Google's current Gemini documentation shows `gemini-3.8-flash` for text, image, and chat generation. The app uses the Python `google-genai` SDK. See: https://ai.google.dev/api/generate-content

Twilio's Python SDK supports sending SMS through `client.messages.create(...)`, and Twilio's WhatsApp API uses WhatsApp-prefixed E.164 addresses such as `whatsapp:+...`. See: https://www.twilio.com/docs/messaging/tutorials/how-to-send-sms-messages and https://www.twilio.com/docs/whatsapp/quickstart

## 📁 Project structure

```text
agri-lens-ai/
├── app.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
└── .streamlit/
    └── secrets.toml.example
```

## 🚀 Run locally

### 1. Clone the repository

```powershell
git clone https://github.com/YOUR_USERNAME/agri-lens-ai.git
cd agri-lens-ai
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Create Streamlit secrets

Copy:

```text
.streamlit/secrets.toml.example
```

to:

```text
.streamlit/secrets.toml
```

Then fill in your real credentials:

```toml
GEMINI_API_KEY = "your-gemini-api-key"

TWILIO_ACCOUNT_SID = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "your-twilio-auth-token"
TWILIO_SMS_FROM = "+12345678900"
TWILIO_WHATSAPP_FROM = "whatsapp:+14155238886"
```

**Never commit `.streamlit/secrets.toml`.** It is excluded by `.gitignore`.

### 5. Start the app

```powershell
streamlit run app.py
```

## 🔑 Getting the credentials

### Gemini

Create a Gemini API key from Google AI Studio and place it in `GEMINI_API_KEY`.

### Twilio SMS

You need:

- Twilio Account SID
- Twilio Auth Token
- A Twilio SMS-capable sender/phone number

Put the sender number in `TWILIO_SMS_FROM` using E.164 format, for example `+12345678900`.

### Twilio WhatsApp

For testing, you can use the **Twilio WhatsApp Sandbox**. The Sandbox sender is commonly represented as:

```text
whatsapp:+14155238886
```

The recipient must complete the Sandbox setup/join process required by Twilio before receiving Sandbox messages.

For production, configure an approved WhatsApp sender in Twilio and use that value for `TWILIO_WHATSAPP_FROM`.

WhatsApp has opt-in and session/template rules. Business-initiated notifications outside an active customer service window generally require an approved template. The app therefore includes a recipient-consent confirmation before sending.

## 📲 Sending flow

```text
Plant image
    ↓
Gemini Vision
    ↓
Conversation
    ↓
Generate Summary
    ↓
┌───────────────┐
│ concise text  │
└───────────────┘
    ↓
 ┌───────┴────────┐
 ↓                ↓
WhatsApp         SMS
 Twilio          Twilio
```

The summary is generated from the current Gemini conversation history. The summary request is made as a separate Gemini generation call so it does not become an extra user turn in the visible agriculture conversation.

## 🧪 Demo flow

For a short project demo:

1. Open AgriLens AI.
2. Upload a clear tomato/chilli/mango/other plant leaf image.
3. Ask: **“What do you notice in this image?”**
4. Ask: **“How serious does this look?”**
5. Ask: **“What should I do first?”**
6. Click **Generate Summary**.
7. Show the generated summary.
8. Enter a recipient number in E.164 format.
9. Confirm recipient consent.
10. Demonstrate **Send via WhatsApp** or **Send via SMS**.

## ⚠️ Important limitations

- A photo cannot reliably confirm a plant disease in every situation.
- Lighting, camera quality, crop variety, and image angle can affect the result.
- AgriLens AI gives visual observations and possible issue categories, not laboratory diagnoses.
- For serious crop loss, widespread symptoms, or uncertain cases, users should consult a local agricultural officer, agronomist, or plant pathology laboratory.
- Messaging requires correctly configured Twilio credentials and sender permissions.
- WhatsApp delivery is subject to Twilio/WhatsApp opt-in, sender, session, and template requirements.
- SMS delivery can incur Twilio charges and may be subject to regional sender regulations.

## ☁️ Deploy on Streamlit Community Cloud

1. Push this repository to a **public GitHub repository**.
2. Open Streamlit Community Cloud.
3. Create a new app from the GitHub repository.
4. Select `app.py` as the main file.
5. Add the same credentials in the app's **Secrets** settings.
6. Deploy.

Do not upload your real `secrets.toml` file to GitHub.

## 🔒 Security

Never hard-code Gemini or Twilio credentials in `app.py`.

Never commit:

```text
.streamlit/secrets.toml
```

If a credential is accidentally exposed, rotate/revoke it from the provider console.

## 📌 Project positioning

AgriLens AI is designed as an agriculture-focused AI Vision chatbot rather than a simple image classifier. Its main interaction is:

**See → Explain → Chat → Summarize → Share**

This makes the project useful for demonstrating multimodal AI, conversational context, generated summaries, and external messaging integration in one Streamlit application.
