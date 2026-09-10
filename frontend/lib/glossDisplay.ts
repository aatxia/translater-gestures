/**
 * Groups a gloss sequence for display: a run of consecutive Phase 16
 * fingerspelling tokens ("FS_<letter>") reads as noise one chip per letter,
 * so it's collapsed into one chip showing the spelled word. Regular glosses
 * are unaffected -- one chip each, same as before Phase 16.
 */
export interface GlossDisplayItem {
  key: string;
  label: string;
  isFingerspell: boolean;
}

const FINGERSPELL_PATTERN = /^FS_.$/u;

function isFingerspellGloss(gloss: string): boolean {
  return FINGERSPELL_PATTERN.test(gloss);
}

export function groupGlossesForDisplay(sequence: string[]): GlossDisplayItem[] {
  const items: GlossDisplayItem[] = [];
  let i = 0;
  while (i < sequence.length) {
    const gloss = sequence[i]!;
    if (!isFingerspellGloss(gloss)) {
      items.push({ key: `${gloss}-${i}`, label: gloss, isFingerspell: false });
      i += 1;
      continue;
    }

    const start = i;
    let word = "";
    while (i < sequence.length && isFingerspellGloss(sequence[i]!)) {
      word += sequence[i]!.slice(3);
      i += 1;
    }
    items.push({
      key: `fs-${start}`,
      label: `🔤 ${word.charAt(0)}${word.slice(1).toLowerCase()}`,
      isFingerspell: true,
    });
  }
  return items;
}
