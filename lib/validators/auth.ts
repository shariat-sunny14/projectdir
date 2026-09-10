import { z } from "zod";

export const signupSchema = z
  .object({
    fullName: z.string().min(2, "Full name is required"),
    email: z.string().email("Valid email is required"),
    phone: z.string().min(6, "Phone is required"),
    employeeId: z.string().optional(),
    departmentId: z.string().min(1, "Department is required"),
    designation: z.string().min(1, "Designation is required"),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string(),
    address: z.string().optional(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

export type SignupInput = z.infer<typeof signupSchema>;

export const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1, "Password is required"),
  remember: z.boolean().optional(),
});

export type LoginInput = z.infer<typeof loginSchema>;

export const requestResetSchema = z.object({
  email: z.string().email("Enter a valid email address"),
});

export const verifyOtpSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  otp: z.string().regex(/^\d{6}$/, "Enter the 6-digit code"),
});

export const resetPasswordWithOtpSchema = z
  .object({
    resetTicket: z.string().min(1),
    password: z.string().min(6, "Password must be at least 6 characters"),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, { message: "Passwords do not match", path: ["confirmPassword"] });
