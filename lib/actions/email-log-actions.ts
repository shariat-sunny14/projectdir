"use server";

import { revalidatePath } from "next/cache";
import { getSession } from "@/lib/auth/session";
import { isAdmin } from "@/lib/permissions";
import { emailLogsRepo } from "@/lib/json-db/repositories";
import { sendEmail } from "@/lib/services/email-service";
import { writeAudit } from "@/lib/services/audit-service";
import { AppError, runAction, type ActionResult } from "@/lib/errors";

export async function resendEmailAction(logId: string): Promise<ActionResult<null>> {
  return runAction(async () => {
    const session = await getSession();
    if (!session || !isAdmin(session.role)) throw new AppError("ERR_FORBIDDEN", "Not authorized.");

    const log = await emailLogsRepo.findById(logId);
    if (!log) throw new AppError("ERR_NOT_FOUND", "Email log not found.");

    await sendEmail(log.to, log.event, log.subject, log.body);
    await writeAudit(session.userId, "Email", "UPDATE", logId, `Resent to ${log.to}`);
    revalidatePath("/admin/email-logs");
    return null;
  });
}
