import type { ReactNode } from "react";
import { Info, Warning, WarningCircle } from "@phosphor-icons/react";

type GuidanceCalloutTone = "info" | "warning" | "research";

type GuidanceCalloutProps = {
  tone: GuidanceCalloutTone;
  title: string;
  children: ReactNode;
};

const toneClasses: Record<GuidanceCalloutTone, string> = {
  info: "border-slate-300 bg-white text-slate-800",
  warning: "border-amber-300 bg-amber-50 text-amber-950",
  research: "border-slate-300 bg-[#f8faf9] text-slate-700",
};

const markerClasses: Record<GuidanceCalloutTone, string> = {
  info: "text-slate-600",
  warning: "text-amber-700",
  research: "text-slate-600",
};

const markerIcon: Record<GuidanceCalloutTone, ReactNode> = {
  info: <Info size={18} weight="bold" />,
  warning: <Warning size={18} weight="bold" />,
  research: <WarningCircle size={18} weight="bold" />,
};

export default function GuidanceCallout({
  tone,
  title,
  children,
}: GuidanceCalloutProps) {
  return (
    <div className={["flex gap-3 border p-4", toneClasses[tone]].join(" ")}>
      <span
        className={[
          "mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center",
          markerClasses[tone],
        ].join(" ")}
        aria-hidden="true"
      >
        {markerIcon[tone]}
      </span>
      <div>
        <p className="text-sm font-semibold">{title}</p>
        <div className="mt-1 text-sm leading-6 opacity-85">{children}</div>
      </div>
    </div>
  );
}
