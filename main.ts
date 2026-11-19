import { copyFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const source = join(process.env.MAKEFUN_BOT_DIR ?? '.', 'POST.json');
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
if (!existsSync(source)) {
  console.error(`POST.json is missing at ${source}`);
  process.exit(1);
}
try {
  const parsed = JSON.parse(readFileSync(source, 'utf8')) as { url?: unknown };
  if (typeof parsed.url !== 'string' || !parsed.url) throw new Error('"url" must be a non-empty string');
} catch (error) {
  console.error(`POST.json is invalid: ${(error as Error).message}`);
  process.exit(1);
}
mkdirSync(outDir, { recursive: true });
copyFileSync(source, join(outDir, 'POST.json'));
