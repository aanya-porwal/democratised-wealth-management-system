import Link from "next/link";
import { Landmark, ArrowRight, ShieldCheck, Sparkles, TrendingUp, PiggyBank, Lock, Cpu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";

const features = [
  {
    icon: TrendingUp,
    title: "Institutional-grade planning",
    description: "Engine-driven goal analysis, Monte Carlo simulations and scenario analysis — computed on the backend, not in your browser.",
  },
  {
    icon: Sparkles,
    title: "Multi-agent AI advisor",
    description: "An explainable conversational coach that reasons across your portfolio, goals and research using a planner-agent-tool pipeline.",
  },
  {
    icon: PiggyBank,
    title: "Goal-first investing",
    description: "Create, prioritise and track goals with live progress, required SIPs and probability of success from a dedicated goal engine.",
  },
  {
    icon: Lock,
    title: "Private by design",
    description: "JWT-based authentication with rotating refresh tokens, rate limiting and scoped APIs. Your data stays yours.",
  },
  {
    icon: ShieldCheck,
    title: "Research-grade security selection",
    description: "Access institutional-style research reports, security comparisons and rankings produced by a dedicated selection engine.",
  },
  {
    icon: Cpu,
    title: "Financial Command Center",
    description: "One workspace uniting portfolio, goals, AI coach, research, market watch, notifications and tasks — all in real time.",
  },
];

const steps = [
  { n: "01", title: "Connect", description: "Tell us about your income, expenses, assets and goals in a conversational onboarding flow." },
  { n: "02", title: "Plan", description: "The engine builds your explainable financial plan — health score, risk profile, allocation and actions." },
  { n: "03", title: "Grow", description: "Track goals, run what-if scenarios and talk to your AI coach as your life changes." },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      {/* Ambient gradient blobs */}
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="absolute -top-40 left-1/2 h-[480px] w-[720px] -translate-x-1/2 rounded-full bg-brand-500/15 blur-[120px]" />
        <div className="absolute top-1/3 -left-40 h-96 w-96 rounded-full bg-navy-500/15 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-96 w-96 rounded-full bg-brand-400/10 blur-[120px]" />
      </div>

      {/* Nav */}
      <header className="relative z-10 mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <div className="flex items-center gap-2">
          <Landmark className="h-7 w-7 text-primary" aria-hidden />
          <span className="text-xl font-bold tracking-tight">Wealth</span>
        </div>
        <div className="flex items-center gap-2">
          <ThemeToggle />
          <Button variant="ghost" asChild>
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild>
            <Link href="/register">Get started</Link>
          </Button>
        </div>
      </header>

      <main className="relative z-10">
        {/* Hero */}
        <section className="mx-auto max-w-7xl px-6 pb-24 pt-20 text-center">
          <div className="mx-auto mb-6 inline-flex items-center gap-2 rounded-full border bg-background/60 px-4 py-1.5 text-xs font-medium text-muted-foreground">
            <Sparkles className="h-3.5 w-3.5 text-primary" aria-hidden />
            AI-powered wealth intelligence
          </div>
          <h1 className="mx-auto max-w-4xl text-4xl font-bold tracking-tight sm:text-6xl">
            Your financial life,{" "}
            <span className="text-gradient">one command center.</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
            Plan, invest and track every goal with an institutional-grade
            financial engine, explainable AI and research-driven insights —
            all in a single interactive workspace.
          </p>
          <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" asChild className="w-full sm:w-auto">
              <Link href="/register">
                Start planning free <ArrowRight className="ml-2 h-4 w-4" aria-hidden />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="w-full sm:w-auto">
              <Link href="/login">Sign in to your dashboard</Link>
            </Button>
          </div>
        </section>

        {/* Features */}
        <section className="mx-auto max-w-7xl px-6 pb-24">
          <h2 className="mb-10 text-center text-3xl font-bold tracking-tight">
            Everything a modern portfolio needs
          </h2>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div
                key={f.title}
                className="group rounded-xl border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
              >
                <div className="mb-4 inline-flex rounded-lg border bg-background p-2.5">
                  <f.icon className="h-5 w-5 text-primary" aria-hidden />
                </div>
                <h3 className="text-base font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {f.description}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section className="mx-auto max-w-7xl px-6 pb-24">
          <h2 className="mb-10 text-center text-3xl font-bold tracking-tight">
            From zero to a full financial plan in minutes
          </h2>
          <div className="grid gap-8 md:grid-cols-3">
            {steps.map((s) => (
              <div key={s.n} className="relative rounded-xl border bg-card p-8">
                <span className="text-gradient text-5xl font-bold">{s.n}</span>
                <h3 className="mt-4 text-lg font-semibold">{s.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{s.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="mx-auto max-w-7xl px-6 pb-24">
          <div className="relative overflow-hidden rounded-2xl border bg-gradient-to-br from-brand-500/10 via-transparent to-navy-500/10 p-10 text-center sm:p-16">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Ready to take control of your wealth?
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
              Join a platform that combines a financial planning engine, research
              engine and an AI advisor behind one elegant interface.
            </p>
            <Button size="lg" className="mt-8" asChild>
              <Link href="/register">
                Create your account <ArrowRight className="ml-2 h-4 w-4" aria-hidden />
              </Link>
            </Button>
          </div>
        </section>
      </main>

      <footer className="relative z-10 border-t">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <div className="flex items-center gap-2">
            <Landmark className="h-5 w-5 text-primary" aria-hidden />
            <span className="text-sm font-semibold">Wealth Management System</span>
          </div>
          <p className="text-xs text-muted-foreground">
            Investment products are subject to market risk. This platform does not
            constitute investment advice.
          </p>
        </div>
      </footer>
    </div>
  );
}
