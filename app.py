import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

MODEL_NAME = "gemini-3.8-flash"

SYSTEM_PROMPT = """
You are AgriLens AI, a careful visual agriculture assistant.

Your job is to help users understand photos of plants, leaves, fruits, stems, or visible crop symptoms and answer follow-up questions about the same image.

For every image analysis:
1. Identify the plant/crop only when the visual evidence supports it. If uncertain, say so.
2. Describe only visible symptoms first.
3. Give a possible issue or disease category, not a guaranteed diagnosis.
4. Explain confidence in simple language.
5. Give practical, low-risk next steps.
6. Mention when an agricultural officer, local expert, or laboratory diagnosis would be appropriate.
7. Never claim that an image alone proves a disease.
8. Do not recommend unsafe chemical mixing, pesticide doses, or restricted chemicals.
9. Keep answers useful for small farmers and home growers.
10. Use simple English. Avoid unnecessary technical jargon.

When the user asks a follow-up question, use the previous conversation and previously uploaded image context.
If the question is unrelated to agriculture or the uploaded plant, politely redirect it.
"""

SUMMARY_PROMPT = """
Create a concise, farmer-friendly summary of the AgriLens AI conversation below.

Include these sections when the information is available:
- Plant/Crop
- Visible Symptoms
- Possible Issue
- Confidence / Uncertainty
- Questions Discussed
- Recommended Next Steps
- When to Seek Expert Help

Rules:
- Summarize only information supported by the conversation.
- Keep possible issues clearly uncertain; never turn an AI visual observation into a confirmed diagnosis.
- Do not invent plant names, symptoms, treatments, measurements, or facts.
- Do not include unsafe pesticide doses, chemical-mixing instructions, or restricted chemical recommendations.
- Keep the summary short enough for SMS/WhatsApp, preferably under 1,500 characters.
- Use plain text and simple bullets. Do not use Markdown tables.
- End with: "AI visual assessment only — not a laboratory diagnosis."
"""

st.set_page_config(
    page_title="AgriLens AI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { background: #f7faf6; }
    .hero {
        padding: 1.4rem 1.5rem;
        border-radius: 22px;
        background: linear-gradient(135deg, #eaf7e8 0%, #f7fcf5 100%);
        border: 1px solid #d7ead2;
        margin-bottom: 1rem;
    }
    .hero h1 { margin: 0; color: #174b2a; font-size: 2.3rem; }
    .hero p { margin: .45rem 0 0; color: #4d6655; font-size: 1.03rem; }
    .badge {
        display: inline-block;
        padding: .28rem .65rem;
        border-radius: 999px;
        background: #dff2dc;
        color: #245c34;
        font-size: .82rem;
        font-weight: 700;
        margin-bottom: .55rem;
    }
    .info-card {
        padding: 1rem;
        border-radius: 16px;
        background: white;
        border: 1px solid #e1e9df;
        margin-bottom: .8rem;
    }
    .small-note { color: #657568; font-size: .86rem; }
    div[data-testid="stChatMessage"] { border-radius: 14px; }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_gemini_client():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing. Add it to Streamlit Secrets.")
    return genai.Client(api_key=api_key)


def create_chat():
    client = get_gemini_client()
    return client.chats.create(
        model=MODEL_NAME,
        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
    )


def ask_gemini(parts):
    try:
        response = st.session_state.chat.send_message(parts)
        return response.text
    except Exception as exc:
        return (
            "Sorry, I couldn't analyze that right now. Please try again. "
            f"Details: {exc}"
        )


def get_twilio_client():
    required = [
        "TWILIO_ACCOUNT_SID",
        "TWILIO_AUTH_TOKEN",
    ]
    missing = [name for name in required if not st.secrets.get(name)]
    if missing:
        raise RuntimeError(
            "Missing Twilio secrets: " + ", ".join(missing)
        )
    return TwilioClient(
        st.secrets["TWILIO_ACCOUNT_SID"],
        st.secrets["TWILIO_AUTH_TOKEN"],
    )


def get_conversation_transcript():
    """Build a compact text transcript from the current Gemini chat history."""
    history = st.session_state.chat.get_history()
    lines = []

    for item in history:
        role = getattr(item, "role", "")
        label = "User" if role == "user" else "AgriLens AI"
        text_parts = []

        for part in getattr(item, "parts", []) or []:
            text_value = getattr(part, "text", None)
            if text_value:
                text_parts.append(text_value.strip())

        if text_parts:
            lines.append(f"{label}: {' '.join(text_parts)}")

    return "\n".join(lines)


def generate_summary():
    transcript = get_conversation_transcript()
    if not transcript.strip():
        raise RuntimeError("There is not enough conversation content to summarize yet.")

    client = get_gemini_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[SUMMARY_PROMPT, "\nConversation:\n" + transcript],
    )
    summary = (response.text or "").strip()
    if not summary:
        raise RuntimeError("Gemini returned an empty summary.")
    return summary


def send_sms(phone_number, summary):
    from_number = st.secrets.get("TWILIO_SMS_FROM")
    if not from_number:
        raise RuntimeError("TWILIO_SMS_FROM is missing from Streamlit Secrets.")

    client = get_twilio_client()
    message = client.messages.create(
        body=summary,
        from_=from_number,
        to=phone_number,
    )
    return message.sid


def send_whatsapp(phone_number, summary):
    from_number = st.secrets.get("TWILIO_WHATSAPP_FROM")
    if not from_number:
        raise RuntimeError("TWILIO_WHATSAPP_FROM is missing from Streamlit Secrets.")

    client = get_twilio_client()
    to_number = phone_number
    if not to_number.startswith("whatsapp:"):
        to_number = f"whatsapp:{to_number}"

    message = client.messages.create(
        body=summary,
        from_=from_number,
        to=to_number,
    )
    return message.sid


def reset_chat():
    st.session_state.chat = create_chat()
    st.session_state.messages = []
    st.session_state.summary = ""


if "chat" not in st.session_state:
    try:
        st.session_state.chat = create_chat()
        st.session_state.messages = []
        st.session_state.summary = ""
    except Exception as exc:
        st.error(str(exc))
        st.stop()

with st.sidebar:
    st.markdown("## 🌱 AgriLens AI")
    st.markdown(
        "A vision-powered agriculture assistant that lets users **upload a plant photo, chat about symptoms, summarize the conversation, and send the summary by SMS or WhatsApp**."
    )
    st.divider()
    st.markdown("### How it works")
    st.markdown(
        "1. 📸 Upload a plant or crop image\n"
        "2. 🔍 AI describes visible symptoms\n"
        "3. 💬 Ask follow-up questions\n"
        "4. 📋 Generate a conversation summary\n"
        "5. 📱 Send it by SMS or WhatsApp"
    )
    st.divider()
    st.caption("Powered by Gemini vision + Twilio • Built with Streamlit")
    if st.button("🔄 Start a new analysis", use_container_width=True):
        reset_chat()
        st.rerun()

st.markdown(
    """
<div class="hero">
    <div class="badge">AI VISION • AGRICULTURE</div>
    <h1>AgriLens AI 🌱</h1>
    <p>Snap a plant. Understand the symptoms. Ask questions. Get a practical action plan — then share the summary.</p>
</div>
""",
    unsafe_allow_html=True,
)

if not st.session_state.messages:
    st.markdown(
        '<div class="info-card"><b>Try this:</b> Upload a clear photo of a leaf and ask '
        '"What do you notice, and what should I do next?"</div>',
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    with st.chat_message(
        message["role"],
        avatar="🌱" if message["role"] == "assistant" else "🧑‍🌾",
    ):
        if message["kind"] == "image":
            st.image(message["content"], use_container_width=True)
        else:
            st.markdown(message["content"])

user_input = st.chat_input(
    "Ask about a plant, or upload a photo...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = (user_input.text or "").strip()
    parts = []

    if photo is not None:
        image_bytes = photo.getvalue()
        st.session_state.messages.append(
            {"role": "user", "kind": "image", "content": image_bytes}
        )
        parts.append(types.Part.from_bytes(data=image_bytes, mime_type=photo.type))

    if text:
        st.session_state.messages.append(
            {"role": "user", "kind": "text", "content": text}
        )
        parts.append(text)
    elif photo is not None:
        parts.append(
            "Analyze this plant/crop image. Describe visible symptoms, give a "
            "possible issue or disease category with uncertainty, and provide "
            "safe practical next steps."
        )

    if photo is not None:
        with st.chat_message("user", avatar="🧑‍🌾"):
            st.image(image_bytes, use_container_width=True)
    if text:
        with st.chat_message("user", avatar="🧑‍🌾"):
            st.markdown(text)

    with st.chat_message("assistant", avatar="🌱"):
        with st.spinner("🔍 AgriLens is examining the image..." if photo else "🌱 AgriLens is thinking..."):
            answer = ask_gemini(parts)
        st.markdown(answer)

    st.session_state.messages.append(
        {"role": "assistant", "kind": "text", "content": answer}
    )

# Sharing section appears after the user has had a conversation with AgriLens.
if st.session_state.messages:
    st.divider()
    st.markdown("### 📋 Conversation Summary & Sharing")
    st.caption(
        "Generate a concise summary of the current AgriLens conversation, then send it to a phone number. Use E.164 format such as +919876543210."
    )

    if st.button("📝 Generate Summary", type="primary", use_container_width=True):
        try:
            with st.spinner("📝 Creating your conversation summary..."):
                st.session_state.summary = generate_summary()
            st.success("Summary generated.")
        except Exception as exc:
            st.error(f"Could not generate the summary: {exc}")

    if st.session_state.summary:
        st.markdown("#### Your summary")
        st.text_area(
            "Summary",
            value=st.session_state.summary,
            height=280,
            label_visibility="collapsed",
        )

        st.markdown("#### 📱 Send summary")
        phone_number = st.text_input(
            "Phone number",
            placeholder="+919876543210",
            help="Enter the recipient number in E.164 format.",
        )
        consent = st.checkbox(
            "I confirm the recipient has agreed to receive this message.",
            value=False,
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("💬 Send via WhatsApp", use_container_width=True):
                if not phone_number.strip():
                    st.warning("Enter a phone number first.")
                elif not consent:
                    st.warning("Please confirm recipient consent before sending.")
                else:
                    try:
                        sid = send_whatsapp(phone_number.strip(), st.session_state.summary)
                        st.success(f"WhatsApp message sent. Message ID: {sid}")
                    except Exception as exc:
                        st.error(f"WhatsApp send failed: {exc}")

        with col2:
            if st.button("📨 Send via SMS", use_container_width=True):
                if not phone_number.strip():
                    st.warning("Enter a phone number first.")
                elif not consent:
                    st.warning("Please confirm recipient consent before sending.")
                else:
                    try:
                        sid = send_sms(phone_number.strip(), st.session_state.summary)
                        st.success(f"SMS sent. Message ID: {sid}")
                    except Exception as exc:
                        st.error(f"SMS send failed: {exc}")

        st.caption(
            "WhatsApp availability depends on your Twilio WhatsApp sender, recipient opt-in, and WhatsApp session/template rules."
        )
