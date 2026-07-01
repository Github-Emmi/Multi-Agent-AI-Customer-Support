"use client";
import { useState } from "react";
import Link from "next/link";
import toast from "react-hot-toast";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";

export function RegisterForm() {
  const { register } = useAuth();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [errors, setErrors] = useState<Partial<typeof form>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const set = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const validate = () => {
    const e: Partial<typeof form> = {};
    if (!form.name.trim()) e.name = "Name is required";
    if (!form.email) e.email = "Email is required";
    else if (!/\S+@\S+\.\S+/.test(form.email)) e.email = "Enter a valid email";
    if (form.password.length < 8) e.password = "Password must be at least 8 characters";
    if (form.password !== form.confirm) e.confirm = "Passwords do not match";
    return e;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const errs = validate();
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setIsSubmitting(true);
    try {
      await register({ name: form.name, email: form.email, password: form.password });
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        "Registration failed. Please try again.";
      toast.error(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
      <Input label="Full name" type="text" value={form.name}
        onChange={set("name")} error={errors.name} placeholder="Jane Smith" required />
      <Input label="Email address" type="email" value={form.email}
        onChange={set("email")} error={errors.email} placeholder="you@example.com"
        autoComplete="email" required />
      <Input label="Password" type="password" value={form.password}
        onChange={set("password")} error={errors.password} placeholder="Min 8 characters"
        autoComplete="new-password" required />
      <Input label="Confirm password" type="password" value={form.confirm}
        onChange={set("confirm")} error={errors.confirm} placeholder="Re-enter password"
        autoComplete="new-password" required />
      <Button type="submit" isLoading={isSubmitting} className="w-full">
        Create account
      </Button>
      <p className="text-center text-sm text-slate-600">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-blue-600 hover:underline">
          Sign in
        </Link>
      </p>
    </form>
  );
}
