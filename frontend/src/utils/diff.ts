type DiffFile = {
  filePath: string;
  lines: string[];
};

export const parseDiff = (diffText: string): DiffFile[] => {
  const lines = diffText.split(/\r?\n/);
  const files: DiffFile[] = [];
  let current: DiffFile | null = null;

  for (const line of lines) {
    if (line.startsWith("diff --git")) {
      if (current) {
        files.push(current);
      }
      const match = line.match(/a\/(.+?) b\/(.+)/);
      const filePath = match ? match[2] : "unknown";
      current = { filePath, lines: [line] };
      continue;
    }
    if (!current) {
      continue;
    }
    current.lines.push(line);
  }
  if (current) {
    files.push(current);
  }
  return files;
};
