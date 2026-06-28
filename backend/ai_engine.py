import os
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
from database import get_session, Alert, init_db

load_dotenv()
init_db()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert cybersecurity analyst assistant embedded
in an AI-powered Endpoint Detection and Response (EDR) system called XEDR.

Your two jobs:
1. EXPLAIN alerts — when given a security alert, explain in plain English what
   is happening, why it is suspicious, what the risk is, and what the user
   should do. Be clear enough for a non-expert to understand.
2. ANSWER questions — when the user asks about security events, answer using
   the context provided. Be helpful, precise, and concise.

Always structure alert explanations as:
- What happened
- Why it is suspicious
- Risk level and potential impact
- Recommended action

Never make up process names or events not in the provided context."""


def explain_alert(alert):
    try:
        prompt = f"""Explain this security alert in plain English:

Alert Type  : {alert.alert_type}
Severity    : {alert.severity}
Risk Score  : {alert.risk_score}/100
Process     : {alert.process}
Description : {alert.description}
Evidence    : {alert.evidence}
Time        : {alert.timestamp}

Provide a clear explanation suitable for a non-expert user."""

        response = client.chat.completions.create(
            model    = MODEL,
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens  = 500,
            temperature = 0.3,
        )
        explanation = response.choices[0].message.content

        session  = get_session()
        db_alert = session.query(Alert).filter(Alert.id == alert.id).first()
        if db_alert:
            db_alert.explained = explanation
            session.commit()
        session.close()

        return explanation

    except Exception as e:
        return f"[AI] Could not generate explanation: {e}"


def explain_latest_alerts(n=3):
    session = get_session()
    alerts  = (session.query(Alert)
                      .filter(Alert.explained == None)
                      .order_by(Alert.timestamp.desc())
                      .limit(n)
                      .all())
    session.close()

    if not alerts:
        print("[AI] No new alerts to explain.")
        return

    print(f"\n[AI] Explaining {len(alerts)} new alert(s)...\n")
    for alert in alerts:
        explanation = explain_alert(alert)
        print(f"{'─'*55}")
        print(f"[AI EXPLANATION] {alert.alert_type} | {alert.severity}")
        print(f"Process : {alert.process}")
        print(f"\n{explanation}")
        print(f"{'─'*55}\n")


def get_recent_context(n=10):
    session = get_session()
    alerts  = (session.query(Alert)
                      .order_by(Alert.timestamp.desc())
                      .limit(n)
                      .all())
    session.close()

    if not alerts:
        return "No alerts recorded yet."

    lines = ["Recent security alerts on this system:\n"]
    for a in alerts:
        lines.append(
            f"- [{a.timestamp.strftime('%H:%M:%S')}] "
            f"{a.severity} | {a.alert_type} | "
            f"Process: {a.process} | Risk: {a.risk_score}/100"
        )
    return "\n".join(lines)


def chat(user_message, conversation_history=None):
    if conversation_history is None:
        conversation_history = []

    context      = get_recent_context()
    full_message = f"""Security context:
{context}

User question: {user_message}"""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += conversation_history.copy()
    messages.append({"role": "user", "content": full_message})

    try:
        response = client.chat.completions.create(
            model       = MODEL,
            messages    = messages,
            max_tokens  = 600,
            temperature = 0.3,
        )
        reply = response.choices[0].message.content

        conversation_history.append({"role": "user",      "content": full_message})
        conversation_history.append({"role": "assistant", "content": reply})

        return reply, conversation_history

    except Exception as e:
        return f"[AI] Error: {e}", conversation_history


def run_chat_terminal():
    print("\n" + "="*55)
    print("  XEDR Security Assistant — Chat Mode")
    print("  Type 'quit' to exit | 'explain' to explain alerts")
    print("="*55 + "\n")

    history = []

    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() == "quit":
                print("Exiting chat.")
                break
            if user_input.lower() == "explain":
                explain_latest_alerts()
                continue

            print("\nAssistant: ", end="", flush=True)
            reply, history = chat(user_input, history)
            print(reply)
            print()

        except KeyboardInterrupt:
            print("\nExiting chat.")
            break


if __name__ == "__main__":
    run_chat_terminal()