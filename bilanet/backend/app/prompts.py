"""Prompts for every BilaNet feature, in one place.

Kept short on purpose: the desktop app runs a 3B model with a 4096-token window on
low-memory laptops, so every token of instruction costs room for the user's code.
"""

# Languages the assistant can explain things in. Code, identifiers and error messages
# always stay as they are; only the explanation text changes language.
# The code is what the frontend sends as `reply_language`.
REPLY_LANGUAGES = {
    "en": "English",
    "sw": "Swahili (Kiswahili)",
    "ha": "Hausa",
    "yo": "Yoruba",
    "ig": "Igbo",
    "am": "Amharic",
    "om": "Oromo (Afaan Oromoo)",
    "so": "Somali",
    "ti": "Tigrinya",
    "zu": "Zulu (isiZulu)",
    "xh": "Xhosa (isiXhosa)",
    "af": "Afrikaans",
    "st": "Sesotho",
    "tn": "Setswana",
    "sn": "Shona (chiShona)",
    "rw": "Kinyarwanda",
    "lg": "Luganda",
    "ak": "Twi (Akan)",
    "wo": "Wolof",
    "ln": "Lingala",
    "mg": "Malagasy",
    "ar": "Arabic",
    "fr": "French",
    "pt": "Portuguese",
}

# Programming languages offered for code generation and translation (10 for translation).
CODE_LANGUAGES = {
    "python": "Python",
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "java": "Java",
    "c": "C",
    "cpp": "C++",
    "csharp": "C#",
    "go": "Go",
    "php": "PHP",
    "sql": "SQL",
    "html": "HTML/CSS",
    "rust": "Rust",
}

BASE_SYSTEM = (
    "You are BilaNet, a friendly coding assistant for developers and students in Africa. "
    "Be concise. Give correct, runnable code in fenced code blocks."
)


def lang_name(code: str | None) -> str:
    return CODE_LANGUAGES.get((code or "").lower(), code or "the same language")


def system_prompt(reply_language: str | None = None, extra: str = "") -> str:
    parts = [BASE_SYSTEM]
    if extra:
        parts.append(extra)
    name = REPLY_LANGUAGES.get((reply_language or "en").lower())
    if name and name != "English":
        parts.append(
            f"Write all explanations in {name}. Keep code, keywords, variable names and "
            "error messages unchanged. If you do not know a technical word in "
            f"{name}, use the English word."
        )
    return " ".join(parts)


# Short reminder added at the END of the user's message. Small models follow the last thing
# they read much better than the system prompt: in a test of 8 questions with the Light
# (1.5B) model, French went from 4/8 to 8/8 answers in French, Portuguese from 4/8 to 8/8.
LANGUAGE_REMINDERS = {
    "fr": "Réponds en français.",
    "pt": "Responde em português.",
    "ar": "أجب باللغة العربية.",
}


def with_reply_language(prompt: str, reply_language: str | None) -> str:
    code = (reply_language or "en").lower()
    name = REPLY_LANGUAGES.get(code)
    if not name or code == "en":
        return prompt
    return f"{prompt}\n\n{LANGUAGE_REMINDERS.get(code, f'Answer in {name}.')}"


def generate(description: str, language: str) -> str:
    return (
        f"Write {lang_name(language)} code for this task:\n{description}\n\n"
        "Give the complete code first, then a short explanation of how to run it."
    )


def explain(code: str, language: str) -> str:
    return (
        f"Explain this {lang_name(language)} code to a beginner, line by line. "
        "For each line or small group of lines, quote it, then say in simple words what it does. "
        "End with a one-sentence summary of what the whole program does.\n\n"
        f"```\n{code}\n```"
    )


def debug(code: str, language: str, error: str | None) -> str:
    err = f"\n\nThe error message is:\n```\n{error}\n```" if error else ""
    return (
        f"Find the bugs in this {lang_name(language)} code (syntax errors and logic errors).{err}\n\n"
        f"```\n{code}\n```\n\n"
        "Answer with: 1) a numbered list of each problem and why it is wrong, "
        "2) the full corrected code."
    )


def optimize(code: str, language: str) -> str:
    return (
        f"Improve this {lang_name(language)} code for performance and readability "
        "without changing what it does.\n\n"
        f"```\n{code}\n```\n\n"
        "Answer with: 1) the improved code, 2) a short bullet list of what you changed and why."
    )


def translate(code: str, source: str, target: str) -> str:
    return (
        f"Translate this {lang_name(source)} code to {lang_name(target)}. "
        f"Use idiomatic {lang_name(target)} and keep the same behaviour.\n\n"
        f"```\n{code}\n```\n\n"
        f"Give the {lang_name(target)} code, then list any differences a learner should notice."
    )


def with_docs(question: str, snippets: list[dict]) -> str:
    """Retrieval-augmented prompt: answer using the offline documentation found."""
    if not snippets:
        return question
    ctx = "\n\n".join(f"[{s['title']}]\n{s['text']}" for s in snippets)
    return (
        "Use this documentation to answer. Mention which function or page you used.\n\n"
        f"{ctx}\n\nQuestion: {question}"
    )


def quiz_challenge(topic: str, level: str) -> str:
    return (
        f"Create one {level} coding challenge about {topic}. "
        "Give: a title, the task description, an example input and output, and a hint. "
        "Do NOT give the solution."
    )


def quiz_check(challenge: str, solution: str, language: str) -> str:
    return (
        f"A student solved this challenge in {lang_name(language)}.\n\n"
        f"Challenge:\n{challenge}\n\nStudent's solution:\n```\n{solution}\n```\n\n"
        "Say whether it is correct (start with CORRECT or NOT YET), point out mistakes kindly, "
        "and give one tip to improve. Show a corrected version only if it is wrong."
    )


def scaffold(description: str, stack: str) -> str:
    return (
        f"Plan a {stack} project for: {description}\n\n"
        "Give: 1) the folder and file tree in a ```text block, "
        "2) the starter code for the most important files, each in its own code block "
        "with the file path on the line before it, 3) the commands to install and run it."
    )
