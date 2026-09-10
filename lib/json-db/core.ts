import fs from "fs/promises";
import path from "path";

const DATA_DIR = path.join(process.cwd(), "data");

// ---- In-process write queue (per-file) to prevent overlapping writes from
// clobbering each other. This is sufficient for a single Node.js process
// serving the MVP; for multi-process deployment a real DB/lock would be needed.
const writeQueues = new Map<string, Promise<unknown>>();

function queued<T>(key: string, fn: () => Promise<T>): Promise<T> {
  const prev = writeQueues.get(key) ?? Promise.resolve();
  const next = prev.then(fn, fn);
  // Store a promise that always resolves so a failure doesn't jam the queue.
  writeQueues.set(
    key,
    next.catch(() => undefined)
  );
  return next;
}

function filePath(name: string): string {
  return path.join(DATA_DIR, `${name}.json`);
}

async function ensureFile(name: string): Promise<void> {
  const p = filePath(name);
  try {
    await fs.access(p);
  } catch {
    await fs.mkdir(DATA_DIR, { recursive: true });
    await fs.writeFile(p, "[]", "utf-8");
  }
}

/** Safe read: auto-creates the file with [] if missing, backs up + resets on corruption. */
export async function readJson<T = unknown>(name: string): Promise<T> {
  await ensureFile(name);
  const p = filePath(name);
  const raw = await fs.readFile(p, "utf-8");
  try {
    return JSON.parse(raw) as T;
  } catch (err) {
    // Corruption handling: back up the bad file, reset to empty array.
    const backupPath = `${p}.corrupt.${Date.now()}.bak`;
    await fs.copyFile(p, backupPath).catch(() => undefined);
    await fs.writeFile(p, "[]", "utf-8");
    return [] as unknown as T;
  }
}

/** Safe write: writes to a temp file then atomically renames over the target. */
async function writeJsonRaw(name: string, data: unknown): Promise<void> {
  await ensureFile(name);
  const p = filePath(name);
  const tmp = `${p}.${process.pid}.${Date.now()}.tmp`;
  await fs.writeFile(tmp, JSON.stringify(data, null, 2), "utf-8");
  await fs.rename(tmp, p);
}

export async function writeJson<T = unknown>(name: string, data: T): Promise<void> {
  await queued(name, () => writeJsonRaw(name, data));
}

/** Read-modify-write, serialized per file so concurrent updates don't clobber each other. */
export async function updateJson<T = unknown>(
  name: string,
  mutator: (current: T) => T | Promise<T>
): Promise<T> {
  return queued(name, async () => {
    const current = await readJson<T>(name);
    const next = await mutator(current);
    await writeJsonRaw(name, next);
    return next;
  });
}

// ---- ID generation -------------------------------------------------------

type CounterPrefix =
  | "USR"
  | "DEP"
  | "VEH"
  | "DRV"
  | "BK"
  | "TRP"
  | "SRV"
  | "EXP"
  | "NOT"
  | "AUD"
  | "EML"
  | "VCH"
  | "OTP"
  | "LOC";

const PAD: Record<CounterPrefix, number> = {
  USR: 3,
  DEP: 3,
  VEH: 3,
  DRV: 3,
  BK: 5,
  TRP: 5,
  SRV: 5,
  EXP: 5,
  NOT: 5,
  AUD: 5,
  EML: 5,
  VCH: 5,
  OTP: 6,
  LOC: 6,
};

export async function nextId(prefix: CounterPrefix): Promise<string> {
  const result = await queued("counters", async () => {
    const counters = await readJson<Record<string, number>>("counters");
    const nextVal = (counters[prefix] ?? 0) + 1;
    counters[prefix] = nextVal;
    await writeJsonRaw("counters", counters);
    return nextVal;
  });
  return `${prefix}-${String(result).padStart(PAD[prefix], "0")}`;
}
