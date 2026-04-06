from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# In-memory conversation history per phone number
conversations = {}

SYSTEM_PROMPT = """You are a booking assistant for Anastasia, a 25-year-old massage therapist based in Limassol, Cyprus.

Business Details:
- Name: Anastasia, 25 years old
- Location: Limassol, Cyprus
- Working Hours: 12:00 to 00:00 (noon to midnight)

Services & Prices (Body2Body massage, totally nude, with oil):
- 1 hour: 110€
- 45 minutes: 80€
- 30 minutes: 60€

Optional Extras:
- Prostate massage: +30€
- Striptease: +20€
- Cum on body: +20€
- Foot fetish: +20€
- Shower together: +20€

Important Rules:
- NO sex services
- NO bikini area services
- Be warm, friendly, and professional
- Detect the customer's language automatically: reply in English if they write in English, reply in Russian if they write in Russian
- Help customers choose a session and book an appointment
- Collect: preferred date, time, duration, and any extras they want
- Always confirm the total price before finalizing
- When booking is confirmed, summarize: service, duration, extras, total price, and appointment time

If a customer asks for the address or location, reply exactly:
"We are located at Limassol Marina, Limassol, Cyprus ❤️ I'll send you the exact pin once your booking is confirmed!"

Keep replies concise and conversational. Never be explicit or crude — stay professional."""


@app.route("/webhook", methods=["POST"])
def webhook():
    from_number = request.form.get("From", "unknown")
    body = request.form.get("Body", "").strip()

    if not body:
        return str(MessagingResponse())

    # Initialize conversation history for new contacts
    if from_number not in conversations:
        conversations[from_number] = []

    conversations[from_number].append({"role": "user", "content": body})

    # Keep last 30 messages to stay within token limits
    history = conversations[from_number][-30:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = "Sorry, I'm having technical difficulties. Please try again in a moment."
        print(f"OpenAI error: {e}")

    conversations[from_number].append({"role": "assistant", "content": reply})

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
