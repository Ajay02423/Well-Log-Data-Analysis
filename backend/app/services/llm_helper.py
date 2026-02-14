from huggingface_hub import InferenceClient
from app.core.config import settings
import time
import json

CANDIDATE_MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
]

def generate_interpretation_text(structured: dict) -> str:
    """
    Generate a cautious, structured AI-assisted interpretation
    based strictly on numerical well-log statistics.
    """

    curve_insights = structured.get("curve_insights", [])

    if not curve_insights:
        return (
            "Insufficient valid numerical data was available in the selected "
            "depth range to generate a reliable interpretation."
        )

    client = InferenceClient(token=settings.HF_API_TOKEN)

    structured_text = json.dumps(structured, indent=2)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert petroleum geoscientist.\n\n"
                "You will be given numerical statistics for multiple well-log curves.\n\n"
                "STRICT RULES:\n"
                "- You MUST comment on EVERY curve provided.\n"
                "- Output EXACTLY ONE subsection per curve.\n"
                "- Do NOT skip or merge curves.\n"
                "- Do NOT assume physical meaning of curve names.\n"
                "- Interpret ONLY statistical behavior (trend, variability, stability).\n"
                "- Keep each curve interpretation to 2–3 sentences.\n"
                "- Clearly state uncertainty when interpretation is limited.\n\n"
                "FORMAT (MANDATORY):\n"
                "## Curve: <CURVE_NAME>\n"
                "- Variability: ...\n"
                "- Trend with depth: ...\n"
                "- Notable observations: ...\n"
                "Do NOT add extra sections or conclusions."
            ),
        },
        {
            "role": "user",
            "content": (
                "Well-log statistical summary (JSON):\n\n"
                f"{structured_text}\n\n"
                "REMINDER:\n"
                "- You must produce one section for each curve in curve_insights.\n"
                "- If interpretation is weak, say so explicitly.\n"
            ),
        },
    ]

    for model_id in CANDIDATE_MODELS:
        try:
            response = client.chat_completion(
                model=model_id,
                messages=messages,
                max_tokens=600,   # Enough for ~6 curves safely
                temperature=0.25,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Warning: Model {model_id} failed ({e}). Trying fallback...")
            time.sleep(1)

    return "Interpretation unavailable (AI service temporarily unavailable)."
