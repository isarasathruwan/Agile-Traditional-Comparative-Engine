import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { validateHumanText } from "@/lib/textValidation";

interface TextQuestionProps {
  question: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  eyebrow?: string;
  helper?: string;
  fieldLabel?: string;
}

const INPUT_CLASSNAME =
  "w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-lg text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-600 focus:ring-4 focus:ring-blue-100";

export default function TextQuestion({
  question,
  placeholder,
  value,
  onChange,
  onSubmit,
  eyebrow,
  helper,
  fieldLabel = "Your response",
}: TextQuestionProps) {
  const displayed = question;
  const typingDone = true;
  const inputRef = useRef<HTMLInputElement>(null);
  const [showHint, setShowHint] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  
  const handleNext = () => {
    const trimmed = value.trim();
    const validationError = validateHumanText(trimmed);
    if (validationError) {
      setErrorMsg(validationError);
      return;
    }
    setErrorMsg(null);
    onSubmit();
  };

  useEffect(() => {
    if (!typingDone) {
      return;
    }

    inputRef.current?.focus();
    const timeout = window.setTimeout(() => setShowHint(true), 120);

    return () => window.clearTimeout(timeout);
  }, [typingDone]);

  return (
    <div className="w-full border-y border-slate-200 bg-white px-5 py-8 sm:border sm:px-10 sm:py-11">
      <div className="min-h-[154px]">
        {eyebrow ? (
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-700">{eyebrow}</p>
        ) : null}
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
          className="max-w-xl space-y-5"
        >
          <label className="block space-y-2">
            <span className="text-sm font-medium text-slate-600">{fieldLabel}</span>
            <input
              ref={inputRef}
              type="text"
              value={value}
              placeholder={placeholder}
              onChange={(event) => {
                onChange(event.target.value);
                if (errorMsg) setErrorMsg(null);
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  handleNext();
                }
              }}
              className={INPUT_CLASSNAME}
            />
          </label>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            {errorMsg ? (
              <p className="text-sm font-medium text-rose-500">{errorMsg}</p>
            ) : showHint ? (
              <p className="text-sm text-slate-500">Press Enter to continue</p>
            ) : (
              <span />
            )}
            <button
              type="button"
              onClick={handleNext}
              disabled={!value.trim()}
              className="rounded-md bg-blue-700 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-800 active:translate-y-px disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              Continue
            </button>
          </div>
        </motion.div>
      ) : null}
    </div>
  );
}
