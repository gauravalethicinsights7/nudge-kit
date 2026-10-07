// Prose -> bullets. Splits on sentence ends, semicolons and em-dashes, but
// never inside an abbreviation ("Dr.", "Ph.D.", "approx.") or a decimal /
// scaled number ("2.7M", "100M+", "~22.7% CAGR"), which is where a naive
// split-on-period mangles pharma copy.

const ABBREVIATIONS = new Set([
  "dr", "drs", "mr", "mrs", "ms", "prof", "ph.d", "phd", "m.d", "md", "b.sc",
  "approx", "est", "etc", "e.g", "i.e", "vs", "no", "fig", "al", "inc", "ltd",
  "co", "corp", "st", "jr", "sr", "u.s", "u.k", "max", "min", "avg", "ca",
]);

function isAbbreviation(textBefore: string): boolean {
  const lastWord = textBefore.split(/[\s(]/).pop() ?? "";
  return ABBREVIATIONS.has(lastWord.toLowerCase().replace(/[^a-z.]/g, ""));
}

function capitalize(s: string): string {
  if (!s) return s;
  return s[0].toUpperCase() + s.slice(1);
}

export function toBullets(prose: string | null | undefined): string[] {
  if (!prose) return [];
  const text = prose.replace(/\s+/g, " ").trim();
  if (!text) return [];

  const out: string[] = [];
  let current = "";

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const next = text[i + 1] ?? "";
    current += ch;

    // Semicolon and em-dash are always clause boundaries.
    if (ch === ";" || ch === "—") {
      out.push(current);
      current = "";
      continue;
    }

    if (ch === "." || ch === "!" || ch === "?") {
      // A digit on either side means it's a decimal, not a sentence end.
      const prev = text[i - 1] ?? "";
      if (ch === "." && (/\d/.test(prev) || /\d/.test(next))) continue;
      // Needs whitespace after it to end a sentence.
      if (next && next !== " ") continue;
      if (ch === "." && isAbbreviation(current.slice(0, -1))) continue;
      out.push(current);
      current = "";
    }
  }

  if (current.trim()) out.push(current);

  return out
    .map((b) => b.replace(/^[\s;—–-]+/, "").replace(/[\s;—]+$/, "").trim())
    .filter((b) => b.length > 1)
    .map(capitalize);
}

// Already-structured list of short strings still deserves the capital-letter
// rule, without being re-split.
export function normalizeBullets(items: (string | null | undefined)[]): string[] {
  return items.filter((s): s is string => !!s && s.trim().length > 0).map((s) => capitalize(s.trim()));
}
