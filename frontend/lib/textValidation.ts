const VOWELS = new Set(["a", "e", "i", "o", "u"]);
const COMMON_SUFFIXES = [
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
];

export function validateHumanText(value: string): string | null {
  const trimmed = value.trim();
  if (trimmed.length < 2) {
    return "Please enter at least 2 characters.";
  }
  if (/(.)\1{4,}/.test(trimmed)) {
    return "Please enter a valid response.";
  }

  const lettersAndNumbers = trimmed.replace(/[^a-zA-Z0-9 ]/g, "");
  if (trimmed.length > 0 && lettersAndNumbers.length / trimmed.length < 0.5) {
    return "Response contains too many symbols.";
  }

  const tokens = trimmed.toLowerCase().split(/\s+/).filter(Boolean);
  for (const token of tokens) {
    if (!/^[a-z]+$/.test(token) || token.length < 8) {
      continue;
    }

    let consonantRun = 0;
    let maxConsonantRun = 0;
    for (const char of token) {
      if (VOWELS.has(char)) {
        consonantRun = 0;
      } else {
        consonantRun += 1;
        maxConsonantRun = Math.max(maxConsonantRun, consonantRun);
      }
    }
    if (maxConsonantRun >= 6) {
      return "Please enter a valid response.";
    }

    const bigrams: string[] = [];
    for (let index = 0; index < token.length - 1; index += 1) {
      bigrams.push(token.slice(index, index + 2));
    }
    const counts = new Map<string, number>();
    for (const bigram of bigrams) {
      counts.set(bigram, (counts.get(bigram) ?? 0) + 1);
    }
    const uniqueBigramRatio = bigrams.length === 0 ? 1 : counts.size / bigrams.length;
    const repeatedBigramShare =
      bigrams.length === 0
        ? 0
        : Array.from(counts.values()).reduce((total, count) => total + Math.max(0, count - 1), 0) / bigrams.length;
    if (uniqueBigramRatio < 0.65 || repeatedBigramShare > 0.4) {
      return "Please enter a valid response.";
    }

    const uniqueCharacterRatio = new Set(token).size / token.length;
    const looksLikeKnownSuffix = COMMON_SUFFIXES.some((suffix) => token.endsWith(suffix));
    if (token === token.toLowerCase() && uniqueCharacterRatio < 0.45 && repeatedBigramShare > 0.2 && !looksLikeKnownSuffix) {
      return "Please enter a valid response.";
    }
  }

  return null;
}
