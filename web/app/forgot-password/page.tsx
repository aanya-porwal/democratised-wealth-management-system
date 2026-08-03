"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Landmark, Loader2, MailCheck } from "lucide-react";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { toast } from "sonner";
import { getErrorMessage } from "@/lib/utils";

const schema = z.object({
  email: z.string().email("Enter a valid email address"),
});

type Values = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { email: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    setSubmitting(true);
    try {
      await api.requestPasswordReset(values.email);
      setSent(true);
      toast.success("If that account exists, a reset link has been sent");
    } catch (err) {
      toast.error(getErrorMessage(err, "Unable to request reset"));
    } finally {
      setSubmitting(false);
    }
  });

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background p-4">
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <div className="absolute -top-32 left-1/2 h-96 w-[640px] -translate-x-1/2 rounded-full bg-brand-500/10 blur-[120px]" />
      </div>

      <Card className="relative w-full max-w-md border bg-card/80 backdrop-blur">
        <CardHeader className="text-center">
          <Link href="/" className="mx-auto mb-2 inline-flex items-center gap-2">
            <Landmark className="h-8 w-8 text-primary" aria-hidden />
          </Link>
          <CardTitle className="text-2xl">Reset your password</CardTitle>
          <CardDescription>
            {sent
              ? "Check your inbox for a link to set a new password."
              : "Enter your email and we'll send you a reset link."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="flex flex-col items-center gap-3 py-6 text-center">
              <MailCheck className="h-12 w-12 text-primary" aria-hidden />
              <p className="text-sm text-muted-foreground">
                If an account exists for that email, instructions are on the way.
              </p>
              <Button variant="outline" asChild className="mt-2">
                <Link href="/login">Back to sign in</Link>
              </Button>
            </div>
          ) : (
            <form onSubmit={onSubmit} className="space-y-4" noValidate>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="you@example.com"
                  aria-invalid={!!errors.email}
                  {...register("email")}
                />
                {errors.email ? (
                  <p className="text-sm text-destructive" role="alert">
                    {errors.email.message}
                  </p>
                ) : null}
              </div>
              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />
                ) : null}
                Send reset link
              </Button>
              <Button variant="ghost" type="button" className="w-full" asChild>
                <Link href="/login">Back to sign in</Link>
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
