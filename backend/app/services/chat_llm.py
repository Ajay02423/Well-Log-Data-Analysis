from huggingface_hub import InferenceClient
from app.core.config import settings
from app.services.chat_memory import get_history, append_user_message, append_assistant_message
import json
import time
import logging
from typing import Any

MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "HuggingFaceTB/SmolLM2-1.7B-Instruct",
]

SYSTEM_PROMPT = """
You are a helpful, concise conversational assistant specialized in well-log analysis.

When the user asks about well-log data, use the provided statistics and only discuss curves
that exist in the data. When the question is general, answer normally. If you need more data,
explicitly ask for it. Do not hallucinate or invent values.
"""


def generate_chat_response(
    question: str,
    structured_data: dict | None,
    selected_curves: list[str] | None,
    conversation_id: str | None = None,
) -> tuple[str, str]:
    """
    Generate a chat response. Returns (text, conversation_id).

    Behavior:
    - Preserves conversation history (follow-ups).
    - Includes a short structured-data summary when the question is data-related.
    - Retries on token/length errors with reduced `max_tokens`.
    """

    client = InferenceClient(token=settings.HF_API_TOKEN)

    def summarize_structured(sd: dict[str, Any]) -> str:
        if not sd:
            return "(no structured data)"
        parts: list[str] = []
        dr = sd.get("depth_range", {})
        parts.append(f"Depth range: {dr.get('min')} - {dr.get('max')} {dr.get('unit', '')}")
        curves = sd.get("curve_insights", [])
        for c in curves[:10]:
            parts.append(
                f"{c.get('curve')}: samples={c.get('samples')}, mean={c.get('mean')}, std={c.get('std')}, trend={c.get('trend')}"
            )
        if len(curves) > 10:
            parts.append(f"...and {len(curves)-10} more curves omitted")
        return "\n".join(parts)

    def is_data_relevant(q: str | None, selected: list[str] | None) -> bool:
        if selected:
            return True
        if not q:
            return False
        ql = q.lower()
        keywords = [
            "curve",
            "curves",
            "depth",
            "trend",
            "mean",
            "std",
            "interpret",
            "analyze",
            "well",
            "log",
            "samples",
            "statistics",
            "compare",
        ]
        for k in keywords:
            if k in ql:
                return True
        if len(ql) > 80:
            return True
        return False

    # Load or create conversation
    conv_id, history = get_history(conversation_id)

    # Helper: build normalized map of available curve names for robust matching
    def _available_curve_map(sd: dict | None) -> dict:
        cmap = {}
        if not sd:
            return cmap
        for c in sd.get("curve_insights", []) or []:
            name = (c or {}).get("curve")
            if not name:
                continue
            # normalized compact form and tokenized form
            norm = "".join(ch for ch in name.lower() if ch.isalnum())
            tokens = ["".join(ch for ch in t if ch.isalnum()) for t in name.lower().split() if t]
            cmap.setdefault(norm, set()).add(name)
            cmap.setdefault(tuple(tokens), set()).add(name)
            # allow common visual variants: 0 <-> o and 2 <-> two
            cmap.setdefault(norm.replace("0", "o"), set()).add(name)
            cmap.setdefault(norm.replace("o", "0"), set()).add(name)
            cmap.setdefault(norm.replace("2", "two"), set()).add(name)
            cmap.setdefault(norm.replace("two", "2"), set()).add(name)
        return cmap

    def _match_requested_from_question(q: str | None, sd_map: dict) -> list[str]:
        if not q or not sd_map:
            return []
        # tokenize question into alphanumeric tokens
        q_tokens = ["".join(ch for ch in t if ch.isalnum()) for t in q.lower().split() if t]
        q_token_set = set(q_tokens)
        q_compact = "".join(q_tokens)

        found = set()

        # check tuple tokens keys first (multi-word curve names)
        for key in list(sd_map.keys()):
            if not key:
                continue
            if isinstance(key, tuple):
                # require all token parts to appear in question tokens
                if all(part in q_token_set for part in key):
                    found.update(sd_map[key])

        # check compact keys (single token names)
        for key, originals in sd_map.items():
            if not key or isinstance(key, tuple):
                continue
            # only match whole tokens for short names (<=2) and exact tokens for longer
            if len(key) <= 2:
                # match only if exactly present as a token (avoid 'ar' matching 'are')
                if key in q_token_set:
                    found.update(originals)
                else:
                    # also check simple visual variants
                    if key.replace("0", "o") in q_token_set or key.replace("o", "0") in q_token_set:
                        found.update(originals)
            else:
                # for longer names, match if token present or compact appears
                if key in q_token_set or key in q_compact:
                    found.update(originals)
                else:
                    # check visual variants
                    if key.replace("0", "o") in q_token_set or key.replace("2", "two") in q_compact:
                        found.update(originals)

        return list(found)

    sd_map = _available_curve_map(structured_data)

    # Build a concise user message. Include a short structured-data summary only when relevant.
    # Determine requested curves from both explicit selection and question text
    requested_from_question = _match_requested_from_question(question, sd_map)
    requested_from_selected: list[str] = []
    missing_selected: list[str] = []
    if selected_curves:
        for s in selected_curves:
            norm = "".join(ch for ch in s.lower() if ch.isalnum())
            matches = sd_map.get(norm) or sd_map.get(norm.replace("0", "o")) or sd_map.get(norm.replace("o", "0"))
            if matches:
                requested_from_selected.extend(list(matches))
            else:
                missing_selected.append(s)

    # Union of requested curves
    relevant_curves = list(dict.fromkeys(requested_from_question + requested_from_selected))

    # If user explicitly requested curves (via question or selected list) but none are present, return an immediate helpful message
    if (requested_from_question or selected_curves) and not relevant_curves:
        available = [next(iter(v)) for k, v in list(sd_map.items())[:40]]
        avail_list = ", ".join(available[:20]) + ("..." if len(available) > 20 else "")
        if requested_from_question:
            reply = f"I couldn't find the requested curve(s) in the dataset. Available curves include: {avail_list}."
        else:
            reply = f"None of the selected curves were found in the dataset. Available curves include: {avail_list}."
        append_assistant_message(conv_id, reply)
        return reply, conv_id

    include_data = bool(relevant_curves)
    user_content = question or ""
    if include_data and structured_data:
        # Summarize only the relevant curves
        sd_subset = {
            "depth_range": structured_data.get("depth_range", {}),
            "curve_insights": [c for c in structured_data.get("curve_insights", []) if c.get("curve") in relevant_curves],
        }
        user_content = f"{user_content}\n\n[WELL_LOG_STATISTICS]\n{summarize_structured(sd_subset)}"

    # Append the user's message to memory (stores a truncated version)
    append_user_message(conv_id, user_content)

    # Prepare messages for the model: system first, then recent history, then current user message
    MAX_HISTORY_MESSAGES = 40
    MAX_MESSAGE_CHARS = 3000
    trimmed_history = history[-MAX_HISTORY_MESSAGES:]
    messages: list[dict[str, str]] = []
    messages.append({"role": "system", "content": SYSTEM_PROMPT})
    for m in trimmed_history:
        c = m.get("content", "")
        if len(c) > MAX_MESSAGE_CHARS:
            c = c[:MAX_MESSAGE_CHARS] + "..."
        messages.append({"role": m.get("role", "user"), "content": c})

    messages.append({"role": "user", "content": user_content})

    # Rough token estimate to avoid provider-side rejections
    approx_input_tokens = sum(len(m.get("content", "")) for m in messages) // 4
    MAX_TOTAL_TOKENS = 32769
    desired_new_tokens = 400
    if approx_input_tokens + desired_new_tokens > MAX_TOTAL_TOKENS:
        desired_new_tokens = max(64, MAX_TOTAL_TOKENS - approx_input_tokens - 50)
        logging.info(
            "[chat_llm] Adjusted desired_new_tokens to %d (approx_input_tokens=%d)",
            desired_new_tokens,
            approx_input_tokens,
        )

    # Try models in order, with retries for token/length related errors
    for model in MODELS:
        token_retry = 0
        while token_retry < 3:
            try:
                response = client.chat_completion(
                    model=model,
                    messages=messages,
                    max_tokens=desired_new_tokens,
                    temperature=0.2,
                )

                text = response.choices[0].message.content.strip()
                combined = text

                # continuation logic: up to 2 follow-ups
                attempts = 0
                while attempts < 2 and (
                    text.endswith("<<CONTINUE>>") or (len(text) > 0 and text[-1] not in ('.', '!', '?'))
                ):
                    if text.endswith("<<CONTINUE>>"):
                        text = text[: -len("<<CONTINUE>>")].rstrip()

                    messages.append({"role": "assistant", "content": text})
                    messages.append({"role": "user", "content": "Please continue the previous answer."})

                    cont_tokens = min(300, desired_new_tokens)
                    response = client.chat_completion(
                        model=model,
                        messages=messages,
                        max_tokens=cont_tokens,
                        temperature=0.2,
                    )

                    text = response.choices[0].message.content.strip()
                    combined += "\n" + text
                    attempts += 1

                append_assistant_message(conv_id, combined.strip())
                return combined.strip(), conv_id

            except Exception as e:
                msg = str(e)
                msg_l = msg.lower()
                logging.warning("Model %s call failed (attempt %d): %s", model, token_retry + 1, msg)

                # If failure looks like a token/length issue, reduce desired_new_tokens and retry
                if (
                    "input validation error" in msg_l
                    or "max_new_tokens" in msg_l
                    or "too long" in msg_l
                    or "exceeded" in msg_l
                    or "422" in msg_l
                    or "413" in msg_l
                ):
                    desired_new_tokens = max(64, desired_new_tokens // 2)
                    logging.info("Reducing desired_new_tokens to %d and retrying", desired_new_tokens)
                    token_retry += 1
                    time.sleep(0.5)
                    continue

                # otherwise give up on this model and try the next one
                break

    logging.error("All models failed to produce a response")
    return "Sorry, I’m temporarily unable to respond.", conv_id
