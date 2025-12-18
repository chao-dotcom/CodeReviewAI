from __future__ import annotations


def base_prompt(role: str, diff: str, context: str) -> str:
    return f"""You are a {role} code reviewer.

Diff:
{diff}

Repository context:
{context}

Return JSON with:
{{"findings":[{{"file_path":"", "line_number":0, "severity":"low|medium|high|critical", "category":"", "description":"", "suggestion":""}}]}}
""".strip()


def critic_prompt(diff: str, reviews: str) -> str:
    return f"""You are a reviewer ranking responses for preference learning.

Diff:
{diff}

Reviews:
{reviews}

Return JSON with:
{{"findings":[{{"file_path":"", "line_number":0, "severity":"info", "category":"preference", "description":"", "suggestion":""}}]}}
""".strip()
