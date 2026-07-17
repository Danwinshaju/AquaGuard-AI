import { useState } from "react";
import { LifeBuoy, LockKeyhole, UserRound } from "lucide-react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ProjectFooter } from "../components/ProjectFooter";

export function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const { user, login, signup } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/analyze" replace />;
  const isSignup = mode === "signup";

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (isSignup) await signup(name, email, password);
      else await login(email, password);
      const requestedPath = (location.state as { from?: string } | null)?.from;
      navigate(requestedPath ?? "/analyze", { replace: true });
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Account request failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <main className="flex flex-1 items-center justify-center px-5 py-12">
        <section className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-7 shadow-xl shadow-slate-200/60 sm:p-9">
          <div className="mb-7 flex items-center gap-3">
            <span className="grid h-12 w-12 place-items-center rounded-2xl bg-ocean-600 text-white"><LifeBuoy size={26} /></span>
            <div><p className="text-xl font-black">AquaGuard AI</p><p className="text-sm text-slate-500">Private incident monitoring</p></div>
          </div>
          <div className="mb-6 rounded-2xl bg-ocean-50 p-4 text-sm text-ocean-900">
            <p className="flex items-center gap-2 font-black"><LockKeyhole size={18} /> Your reports stay private</p>
            <p className="mt-1 leading-6">You can only view, update, export, or delete incidents created by your own account.</p>
          </div>
          <h1 className="text-3xl font-black">{isSignup ? "Create your account" : "Welcome back"}</h1>
          <p className="mt-2 text-slate-500">{isSignup ? "Register before starting video or live-camera analysis." : "Log in to open your AquaGuard workspace."}</p>
          <form className="mt-7 space-y-4" onSubmit={submit}>
            {isSignup && <label className="block text-sm font-bold">Full name<input className="mt-1.5 w-full rounded-xl border border-slate-300 px-4 py-3 font-normal outline-none focus:border-ocean-500 focus:ring-2 focus:ring-ocean-100" autoComplete="name" required minLength={2} maxLength={80} value={name} onChange={(event) => setName(event.target.value)} /></label>}
            <label className="block text-sm font-bold">Email address<input className="mt-1.5 w-full rounded-xl border border-slate-300 px-4 py-3 font-normal outline-none focus:border-ocean-500 focus:ring-2 focus:ring-ocean-100" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} /></label>
            <label className="block text-sm font-bold">Password<input className="mt-1.5 w-full rounded-xl border border-slate-300 px-4 py-3 font-normal outline-none focus:border-ocean-500 focus:ring-2 focus:ring-ocean-100" type="password" autoComplete={isSignup ? "new-password" : "current-password"} required minLength={isSignup ? 8 : 1} maxLength={128} value={password} onChange={(event) => setPassword(event.target.value)} /><span className="mt-1 block text-xs font-normal text-slate-500">{isSignup ? "Use at least 8 characters." : ""}</span></label>
            {error && <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm font-bold text-red-800" role="alert">{error}</p>}
            <button className="flex w-full items-center justify-center gap-2 rounded-xl bg-ocean-600 px-4 py-3.5 font-black text-white hover:bg-ocean-700 disabled:opacity-60" disabled={busy} type="submit"><UserRound size={19} />{busy ? "Please wait…" : isSignup ? "Create account" : "Log in"}</button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-600">{isSignup ? "Already registered?" : "New to AquaGuard?"} <Link className="font-black text-ocean-700 underline" to={isSignup ? "/login" : "/signup"}>{isSignup ? "Log in" : "Create an account"}</Link></p>
        </section>
      </main>
      <ProjectFooter />
    </div>
  );
}
