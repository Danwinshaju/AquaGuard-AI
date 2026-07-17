import type { ReactNode } from "react";
import { BarChart3, BookOpen, BrainCircuit, Camera, Cctv, FileVideo2, LifeBuoy, LogOut, ShieldAlert } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import { ProjectFooter } from "./ProjectFooter";
import { useAuth } from "../auth/AuthContext";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-bold ${
      isActive ? "bg-ocean-600 text-white" : "text-slate-600 hover:bg-slate-100"
    }`;
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-5 py-4">
          <div className="flex items-center gap-3 font-black">
            <span className="grid h-10 w-10 place-items-center rounded-xl bg-ocean-600 text-white">
              <LifeBuoy size={22} />
            </span>
            AquaGuard AI
          </div>
          <nav className="flex max-w-full flex-wrap gap-1" aria-label="Main navigation">
            <NavLink to="/analyze" className={linkClass}><FileVideo2 size={17} /> Analyse</NavLink>
            <NavLink to="/live" className={linkClass}><Camera size={17} /> Live</NavLink>
            <NavLink to="/cameras" className={linkClass}><Cctv size={17} /> Cameras</NavLink>
            <NavLink to="/dashboard" className={linkClass}><BarChart3 size={17} /> Dashboard</NavLink>
            <NavLink to="/incidents" className={linkClass}><ShieldAlert size={17} /> Incidents</NavLink>
            <NavLink to="/model" className={linkClass}><BrainCircuit size={17} /> Train AI</NavLink>
            <NavLink to="/documentation" className={linkClass}><BookOpen size={17} /> Documentation</NavLink>
            <button className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-bold text-red-700 hover:bg-red-50" type="button" title={user?.email} onClick={async () => { await logout(); navigate("/login"); }}><LogOut size={17} /> Log out</button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-5 py-8">{children}</main>
      <ProjectFooter />
    </div>
  );
}
