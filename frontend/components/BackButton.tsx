import { CaretLeft } from "@phosphor-icons/react";

interface BackButtonProps {
  onClick: () => void;
}

export default function BackButton({ onClick }: BackButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Go back"
      className="inline-flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium text-slate-600 transition-colors hover:bg-blue-50 hover:text-blue-700 active:translate-y-px"
    >
      <CaretLeft size={16} weight="bold" />
      Back
    </button>
  );
}
