import { motion } from "framer-motion";
import { useState } from "react";

interface LikertScreenProps {
  construct: string;
  question: string;
  scaleLabels: [string, string, string, string, string];
  initialValue?: number;
  onSelect: (value: number) => void;
  helper?: string;
}

const SCALE_VALUES = [1, 2, 3, 4, 5] as const;

export default function LikertScreen({
  construct,
  question,
  scaleLabels,
  initialValue,
  onSelect,
  helper,
}: LikertScreenProps) {
  const displayed = question;
  const typingDone = true;
  const [selected, setSelected] = useState<number | null>(initialValue ?? null);
  const [lockedAfterSelect, setLockedAfterSelect] = useState(false);

  const choicesLocked = lockedAfterSelect && selected !== null;

  const handleSelect = (value: number) => {
    setSelected(value);
    setLockedAfterSelect(true);
    onSelect(value);
  };

  return (
    <div className="w-full border-y border-slate-200 bg-white px-5 py-8 sm:border sm:px-10 sm:py-11">
      <div className="min-h-[154px]">
        <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">
          {construct}
        </p>
        <h2 className="mt-3 max-w-2xl text-3xl font-semibold tracking-tight text-slate-950 sm:text-[2.15rem]">
          {displayed}
        </h2>
        {helper ? <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">{helper}</p> : null}
      </div>

      {typingDone ? (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.22 }}
        >
          <div className="max-w-2xl border-y border-slate-200 py-5 sm:border-x sm:px-5">
            <div className="mb-3 flex items-center justify-between text-xs font-medium text-slate-500">
              <span className="max-w-[46%] leading-4">{scaleLabels[0]}</span>
              <span className="max-w-[46%] text-right leading-4">{scaleLabels[4]}</span>
            </div>
            <div className="grid grid-cols-5 gap-3">
              {SCALE_VALUES.map((value) => (
                <button
                  key={value}
                  type="button"
                  disabled={choicesLocked}
                  onClick={() => handleSelect(value)}
                  className={`flex h-14 items-center justify-center rounded-md border text-base font-semibold transition-all duration-200 ${
                    selected === value
                      ? "border-blue-700 bg-blue-700 text-white"
                    : choicesLocked
                      ? "border-slate-200 text-slate-400"
                        : "border-slate-200 bg-white text-slate-700 hover:border-blue-400 hover:bg-blue-50 hover:text-blue-800"
                  }`}
                >
                  {value}
                </button>
              ))}
            </div>
            <div className="mt-3 grid grid-cols-5 gap-3 text-center text-[11px] font-medium text-slate-500">
              {SCALE_VALUES.map((value) => (
                <span key={`label-${value}`} className="truncate" title={scaleLabels[value - 1]}>
                  {selected === value ? scaleLabels[value - 1] : value === 3 ? scaleLabels[2] : value}
                </span>
              ))}
            </div>
          </div>
        </motion.div>
      ) : null}
    </div>
  );
}
