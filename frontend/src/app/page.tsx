import Link from "next/link";
import { ArrowRight, Briefcase, Sparkles, Target } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#fafafa] dark:bg-slate-950 font-sans selection:bg-indigo-100 selection:text-indigo-900 overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-6xl h-[500px] bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none animate-float" />

      <main className="relative max-w-5xl mx-auto px-6 pt-32 pb-20 flex flex-col items-center text-center">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 text-sm font-medium mb-8 border border-indigo-100 dark:border-indigo-500/20">
          <Sparkles className="w-4 h-4" />
          The future of job searching is here
        </div>

        {/* Hero Title */}
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight text-slate-900 dark:text-slate-50 mb-6">
          Find your next <span className="text-indigo-600 dark:text-indigo-400">career milestone</span> with precision.
        </h1>

        {/* Subtitle */}
        <p className="text-slate-500 dark:text-slate-400 text-lg md:text-xl max-w-2xl mb-10 leading-relaxed">
          Job Spot uses intelligent matching to pair you with roles that actually fit your skill set. No more endless scrolling. Just results.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4">
          <Link href="/register">
            <Button size="lg" className="h-14 px-8 rounded-2xl text-lg font-semibold bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 shadow-xl hover:shadow-indigo-500/10 transition-all hover:-translate-y-1">
              Get Started Free
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </Link>
          <Link href="/login">
            <Button variant="ghost" size="lg" className="h-14 px-8 rounded-2xl text-lg font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800">
              Sign In
            </Button>
          </Link>
        </div>

        {/* Stats / Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-32 w-full">
          {[
            { icon: Target, title: "Precision Matching", desc: "95% accuracy in matching your skills with job requirements." },
            { icon: Briefcase, title: "Top Companies", desc: "Access to hidden roles at leading tech startups and enterprises." },
            { icon: Sparkles, title: "Smart Tracking", desc: "Keep track of every application status with automated reminders." },
          ].map((item, i) => (
            <div key={i} className="p-8 rounded-3xl bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 text-left hover:border-indigo-100 dark:hover:border-indigo-500/20 transition-colors group">
              <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                <item.icon className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
              </div>
              <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-50 mb-2">{item.title}</h3>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </main>

      {/* Footer Branding */}
      <footer className="relative max-w-5xl mx-auto px-6 py-12 border-t border-slate-100 dark:border-slate-800 flex flex-col md:flex-row justify-between items-center gap-6 opacity-50 text-sm text-slate-500 dark:text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-indigo-600 flex items-center justify-center text-white font-bold text-[10px]">JS</div>
          Job Spot © 2024
        </div>
        <div className="flex gap-8">
          <a href="#" className="hover:text-indigo-600">Privacy</a>
          <a href="#" className="hover:text-indigo-600">Terms</a>
          <a href="#" className="hover:text-indigo-600">Contact</a>
        </div>
      </footer>
    </div>
  );
}
