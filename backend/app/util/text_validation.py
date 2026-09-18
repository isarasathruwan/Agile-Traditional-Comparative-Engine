import re


VOWELS = set("aeiou")
COMMON_SUFFIXES = (
    "tion",
    "ment",
    "ness",
    "ship",
    "able",
    "ible",
    "ance",
    "ence",
    "ing",
    "ers",
    "ies",
    "ism",
    "ist",
    "ity",
    "ary",
    "ory",
)


def validate_human_text(value: str) -> str | None:
    trimmed = value.strip()
    if len(trimmed) < 2:
        return "Must be at least 2 characters"
    if re.search(r"(.)\1{4,}", trimmed):
        return "Contains excessive repeating characters"

    letters_and_numbers = sum(1 for char in trimmed if char.isalnum() or char.isspace())
    if trimmed and (letters_and_numbers / len(trimmed)) < 0.5:
        return "Contains excessive symbols"

    tokens = [token for token in re.split(r"\s+", trimmed.lower()) if token]
    for token in tokens:
        if not token.isalpha() or len(token) < 8:
            continue
        max_consonant_run = 0
        consonant_run = 0
        for char in token:
            if char in VOWELS:
                consonant_run = 0
            else:
                consonant_run += 1
                max_consonant_run = max(max_consonant_run, consonant_run)
        if max_consonant_run >= 6:
            return "Please enter a valid response"

        bigrams = [token[index : index + 2] for index in range(len(token) - 1)]
        if bigrams:
            unique_bigram_ratio = len(set(bigrams)) / len(bigrams)
            repeated_bigram_share = sum(
                count - 1 for count in {item: bigrams.count(item) for item in set(bigrams)}.values()
            ) / len(bigrams)
            if unique_bigram_ratio < 0.65 or repeated_bigram_share > 0.4:
                return "Please enter a valid response"
            unique_character_ratio = len(set(token)) / len(token)
            looks_like_known_suffix = token.endswith(COMMON_SUFFIXES)
            if (
                token.islower()
                and unique_character_ratio < 0.45
                and repeated_bigram_share > 0.2
                and not looks_like_known_suffix
            ):
                return "Please enter a valid response"
    return None
