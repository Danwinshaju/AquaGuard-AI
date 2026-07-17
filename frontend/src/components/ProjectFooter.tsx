import { Github, Linkedin, Mail } from "lucide-react";

export function ProjectFooter() {
  return (
    <footer className="border-t border-slate-200 bg-white px-5 py-6">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 text-center sm:flex-row sm:text-left">
        <div>
          <p className="text-sm font-black text-slate-800">
            © {new Date().getFullYear()} Danwin Shaju. All rights reserved.
          </p>
          <p className="mt-1 text-xs text-slate-500">
            AquaGuard AI · Educational early-warning project · Not a certified safety device
          </p>
        </div>
        <nav className="flex flex-wrap justify-center gap-2 text-sm font-bold" aria-label="Developer profiles">
          <a className="flex items-center gap-2 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-ocean-700" href="mailto:danwin212@gmail.com"><Mail size={17} /> Email</a>
          <a className="flex items-center gap-2 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-ocean-700" href="https://github.com/Danwinshaju" target="_blank" rel="noreferrer"><Github size={17} /> GitHub</a>
          <a className="flex items-center gap-2 rounded-lg px-3 py-2 text-slate-600 hover:bg-slate-100 hover:text-ocean-700" href="https://www.linkedin.com/in/danwin-shaju/" target="_blank" rel="noreferrer"><Linkedin size={17} /> LinkedIn</a>
        </nav>
      </div>
    </footer>
  );
}
