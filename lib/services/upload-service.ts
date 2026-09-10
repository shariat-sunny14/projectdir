import fs from "fs/promises";
import path from "path";
import crypto from "crypto";

const UPLOAD_DIR = path.join(process.cwd(), "public", "uploads");
const ALLOWED_EXT = [".jpg", ".jpeg", ".png", ".pdf"];
const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

/** Saves an uploaded File (from a Server Action's FormData) to /public/uploads with a
 * generated unique name. Returns the public path (e.g. "/uploads/xxxx.pdf"), or
 * undefined if no file / an empty file was provided. Throws on disallowed type/size. */
export async function saveUploadedFile(file: File | null | undefined): Promise<string | undefined> {
  if (!file || file.size === 0) return undefined;

  const ext = path.extname(file.name).toLowerCase();
  if (!ALLOWED_EXT.includes(ext)) {
    throw new Error(`Unsupported file type "${ext}". Allowed: JPG, JPEG, PNG, PDF.`);
  }
  if (file.size > MAX_SIZE_BYTES) {
    throw new Error("File is too large (max 10MB).");
  }

  await fs.mkdir(UPLOAD_DIR, { recursive: true });
  const uniqueName = `${Date.now()}-${crypto.randomBytes(6).toString("hex")}${ext}`;
  const buffer = Buffer.from(await file.arrayBuffer());
  await fs.writeFile(path.join(UPLOAD_DIR, uniqueName), buffer);

  return `/uploads/${uniqueName}`;
}
