import { redirect } from "next/navigation";

// Password reset is now handled entirely by the OTP flow at /forgot-password.
// This route stays only so old bookmarked/emailed links don't 404.
export default function ResetPasswordPage() {
  redirect("/forgot-password");
}
