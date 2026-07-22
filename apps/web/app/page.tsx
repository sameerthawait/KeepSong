import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-slate-950 text-slate-100 font-sans">
      <div className="max-w-xl text-center space-y-6">
        <h1 className="text-5xl font-extrabold tracking-tight bg-gradient-to-r from-amber-200 via-rose-300 to-indigo-300 bg-clip-text text-transparent">
          Keepsong
        </h1>
        <p className="text-slate-300 text-lg">
          Preserving voice, memories, and identity for individuals with dementia.
        </p>

        <div className="pt-8 flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/checkin"
            className="px-6 py-4 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-lg transition shadow-lg shadow-amber-500/20"
          >
            Patient Check-In
          </Link>
          <Link
            href="/dashboard"
            className="px-6 py-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-lg transition shadow-lg shadow-indigo-600/20"
          >
            Caregiver Dashboard
          </Link>
        </div>
      </div>
    </main>
  );
}
