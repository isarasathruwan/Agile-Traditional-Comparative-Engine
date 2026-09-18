interface ProgressBarProps {
  currentScreen: number;
  totalQuestions: number;
  profileQuestions: number;
}

export default function ProgressBar({ currentScreen, totalQuestions, profileQuestions }: ProgressBarProps) {
  const currentStep = Math.min(Math.max(currentScreen, 1), totalQuestions);
  const progress = Math.round((currentStep / Math.max(totalQuestions, 1)) * 100);
  const isProfile = currentStep <= profileQuestions;

  return (
    <div className="flex items-center gap-3 text-right">
      <div className="hidden sm:block">
        <p className="text-xs font-medium text-slate-500">{isProfile ? "Project context" : "Method fit"}</p>
        <p className="mt-0.5 text-xs font-semibold text-slate-900">{currentStep} of {totalQuestions}</p>
      </div>
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-slate-200 sm:w-24" aria-label={`${progress}% complete`} role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress}>
        <div className="h-full rounded-full bg-blue-600 transition-[width] duration-300 ease-out" style={{ width: `${progress}%` }} />
      </div>
      <span className="font-mono text-xs font-semibold text-blue-700">{progress}%</span>
    </div>
  );
}
