"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  ClipboardText,
  DownloadSimple,
  Gauge,
  List,
  ListChecks,
  SignOut,
  SlidersHorizontal,
  Users,
  X,
} from "@phosphor-icons/react";
import { PRODUCT_NAME, type AdminSectionKey } from "@/lib/pageMeta";

export type AdminWorkspaceSection = {
  key: AdminSectionKey;
  label: string;
  advancedOnly: boolean;
};

type Props = {
  activeSection: AdminSectionKey;
  sections: AdminWorkspaceSection[];
  uiMode: "guided" | "advanced";
  onNavigate: (section: AdminSectionKey) => void;
  onToggleUiMode: () => void;
  onSignOut: () => void;
  canExport?: boolean;
  onExport?: () => void;
  children: ReactNode;
};

function SectionIcon({ section, size = 18 }: { section: AdminSectionKey; size?: number }) {
  const props = { size, weight: "duotone" as const };
  if (section === "overview") return <Gauge {...props} />;
  if (section === "assessments") return <ClipboardText {...props} />;
  if (section === "rules") return <SlidersHorizontal {...props} />;
  if (section === "questionnaire") return <ListChecks {...props} />;
  return <Users {...props} />;
}

export default function AdminWorkspaceShell({
  activeSection,
  sections,
  uiMode,
  onNavigate,
  onToggleUiMode,
  onSignOut,
  canExport = false,
  onExport,
  children,
}: Props) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const visibleSections = sections.filter((section) => uiMode === "advanced" || !section.advancedOnly);

  useEffect(() => {
    if (!mobileMenuOpen) return;
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMobileMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [mobileMenuOpen]);

  const navigate = (section: AdminSectionKey) => {
    onNavigate(section);
    setMobileMenuOpen(false);
  };

  const navigation = (
    <nav className="space-y-6" aria-label="Admin sections">
      <div className="space-y-1.5">
        <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Workspace</p>
        {visibleSections.filter((section) => !section.advancedOnly).map((section) => (
          <NavigationLink key={section.key} section={section} active={activeSection === section.key} onClick={() => navigate(section.key)} />
        ))}
      </div>
      {visibleSections.some((section) => section.advancedOnly) ? (
        <div className="space-y-1.5">
          <p className="px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Administration</p>
          {visibleSections.filter((section) => section.advancedOnly).map((section) => (
            <NavigationLink key={section.key} section={section} active={activeSection === section.key} onClick={() => navigate(section.key)} />
          ))}
        </div>
      ) : null}
    </nav>
  );

  const workspaceControls = (
    <div className="space-y-2">
      <button
        type="button"
        onClick={onToggleUiMode}
        className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-left text-sm font-semibold text-slate-700 transition hover:border-emerald-300 hover:bg-emerald-50 active:translate-y-px"
      >
        <span>{uiMode === "guided" ? "Show advanced tools" : "Advanced tools on"}</span>
        <span className={`h-2 w-2 rounded-full ${uiMode === "advanced" ? "bg-emerald-600" : "bg-slate-300"}`} aria-hidden="true" />
      </button>
      {canExport && onExport ? (
        <button type="button" onClick={onExport} className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 active:translate-y-px">
          <DownloadSimple size={18} weight="duotone" />
          Download CSV
        </button>
      ) : null}
    </div>
  );

  const accountControls = (
    <div className="border-t border-slate-200 pt-4">
      <button type="button" onClick={onSignOut} className="flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-rose-50 hover:text-rose-700 active:translate-y-px">
        <SignOut size={18} weight="duotone" />
        Sign out
      </button>
    </div>
  );

  return (
    <div className="grid h-[100dvh] overflow-hidden bg-slate-50 text-slate-900 lg:grid-cols-[248px_minmax(0,1fr)]">
      <aside className="hidden h-full min-h-0 border-r border-slate-200 bg-white lg:flex lg:flex-col lg:px-4 lg:py-5">
        <div className="flex items-center gap-3 px-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-700 text-sm font-bold text-white">M</span>
          <div>
            <p className="text-sm font-semibold tracking-tight text-slate-950">{PRODUCT_NAME}</p>
            <p className="text-xs text-slate-500">Admin workspace</p>
          </div>
        </div>
        <div className="mt-6 px-1">{workspaceControls}</div>
        <div className="min-h-0 flex-1 overflow-y-auto py-6">{navigation}</div>
        {accountControls}
      </aside>

      <div className="grid h-full min-h-0 min-w-0 grid-rows-[auto_minmax(0,1fr)] lg:grid-rows-[minmax(0,1fr)]">
        <header className="flex h-16 items-center border-b border-slate-200 bg-white px-4 lg:hidden">
          <button
            ref={menuButtonRef}
            type="button"
            aria-expanded={mobileMenuOpen}
            aria-controls="admin-mobile-navigation"
            onClick={() => setMobileMenuOpen(true)}
            className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 text-slate-700 transition hover:bg-slate-100 active:translate-y-px"
          >
            <List size={20} aria-hidden="true" />
            <span className="sr-only">Open navigation menu</span>
          </button>
          <p className="ml-3 text-sm font-semibold text-slate-950">{PRODUCT_NAME}</p>
        </header>
        <main id="admin-workspace-content" className="min-h-0 overflow-y-auto overscroll-contain">{children}</main>
      </div>

      {mobileMenuOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Admin navigation">
          <button type="button" className="absolute inset-0 bg-slate-950/35" onClick={() => setMobileMenuOpen(false)} aria-label="Close navigation menu" />
          <aside id="admin-mobile-navigation" className="relative flex h-full w-[min(20rem,calc(100vw-3rem))] flex-col border-r border-slate-200 bg-white px-4 py-5 shadow-[16px_0_40px_-24px_rgba(15,23,42,0.45)]">
            <div className="flex items-center justify-between px-3">
              <div><p className="text-sm font-semibold text-slate-950">{PRODUCT_NAME}</p><p className="text-xs text-slate-500">Admin workspace</p></div>
              <button type="button" onClick={() => setMobileMenuOpen(false)} className="inline-flex h-9 w-9 items-center justify-center rounded-xl text-slate-600 hover:bg-slate-100" aria-label="Close navigation menu"><X size={19} /></button>
            </div>
            <div className="mt-6 px-1">{workspaceControls}</div>
            <div className="min-h-0 flex-1 overflow-y-auto py-6">{navigation}</div>
            {accountControls}
          </aside>
        </div>
      ) : null}
    </div>
  );
}

function NavigationLink({ section, active, onClick }: { section: AdminWorkspaceSection; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition active:translate-y-px ${active ? "bg-emerald-700 text-white shadow-[0_12px_28px_-20px_rgba(4,120,87,0.72)]" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"}`}
    >
      <SectionIcon section={section.key} />
      {section.label}
    </button>
  );
}
