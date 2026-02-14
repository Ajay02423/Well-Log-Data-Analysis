import re

def classify_question(question: str) -> str:
    q = question.lower()

    if "available curve" in q:
        return "curve_list"
    if "depth range" in q:
        return "depth_info"
    if "compare" in q:
        return "compare"
    if "trend" in q or "vary" in q:
        return "trend"
    return "general"


def extract_depth_range(text: str):
    nums = list(map(float, re.findall(r"\d+\.?\d*", text)))
    if len(nums) >= 2:
        return nums[0], nums[1]
    return None, None
