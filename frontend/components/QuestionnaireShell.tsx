"use client";

import { ClipboardText } from "@phosphor-icons/react";
import { ReactNode } from "react";

interface QuestionnaireShellProps {
  header: ReactNode;
  main: ReactNode;
  aside: ReactNode;
  centerMain?: boolean;
  mainWidth?: "standard" | "wide";
}

export default function QuestionnaireShell({
  header,
  main,
  aside,
  centerMain = false,
  mainWidth = "standard",
}: QuestionnaireShellProps) {
  return (
    <main className="min-h-[100dvh] bg-[#f6f8fc] text-slate-900">
      <div
        className={`mx-auto flex min-h-[100dvh] flex-col px-4 sm:px-6 lg:px-8 ${
          mainWidth === "wide"
            ? "max-w-none lg:ml-auto lg:mr-4 lg:max-w-[calc((100vw+1440px)/2-16px)]"
            : "max-w-[1240px]"
        }`}
      >
        <header className="sticky top-0 z-20 -mx-4 flex min-h-20 items-center border-b border-slate-200/90 bg-[#f6f8fc]/95 px-4 py-4 backdrop-blur-sm sm:-mx-6 sm:px-6 lg:-mx-8 lg:px-8">
          <div className="flex w-full items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-700 text-white">
              <ClipboardText size={19} weight="bold" />
            </div>
            <div className="min-w-0">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">MethodAlign</p>
              <p className="truncate text-sm font-medium text-slate-600">Project methodology assessment</p>
            </div>
            <div className="ml-auto">{header}</div>
          </div>
        </header>

        <div
          className={`grid flex-1 gap-8 py-7 lg:gap-12 lg:py-10 ${
            mainWidth === "wide"
              ? "lg:grid-cols-[190px_minmax(0,1fr)]"
              : "lg:grid-cols-[190px_minmax(0,760px)] lg:justify-center"
          }`}
        >
          <aside className="order-2 border-t border-slate-200 pt-5 lg:sticky lg:top-28 lg:order-1 lg:self-start lg:border-t-0 lg:border-r lg:pt-0 lg:pr-7">
            {aside}
          </aside>
          <section className={centerMain ? "order-1 flex min-h-[calc(100dvh-11rem)] items-center lg:order-2" : "order-1 lg:order-2"}>
            <div className="w-full">{main}</div>
          </section>
        </div>
      </div>
    </main>
  );
}
