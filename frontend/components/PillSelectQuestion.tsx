import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { validateHumanText } from "@/lib/textValidation";

interface PillSelectQuestionProps {
  question: string;
  options: string[];
  initialValue?: string;
  initialOtherValue?: string;
  onSelect: (value: string, otherValue?: string) => void;
  onOtherValueChange?: (value: string) => void;
  eyebrow?: string;
  helper?: string;
}

const INPUT_CLASSNAME =
  "w-full rounded-lg border border-slate-300 bg-white px-4 py-3 text-lg text-slate-900 outline-none transition-colors placeholder:text-slate-400 focus:border-blue-600 focus:ring-4 focus:ring-blue-100";

export default function PillSelectQuestion({
  question,
  options,
  initialValue,
  initialOtherValue,
  onSelect,
  onOtherValueChange,
  eyebrow,
  helper,
}: PillSelectQuestionProps) {
  const displayed = question;
  const typingDone = true;
  const [selected, setSelected] = useState<string | null>(initialValue ?? null);
  const [otherValue, setOtherValue] = useState(initialOtherValue ?? "");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isAdvancing, setIsAdvancing] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const otherOption = options.find((option) => option.trim().toLowerCase() === "other");
  const isOtherSelected = Boolean(otherOption && selected === otherOption);

  useEffect(() => {
    if (!typingDone || !isOtherSelected) {
      return;
    }
    const timeout = window.setTimeout(() => inputRef.current?.focus(), 120);
    return () => window.clearTimeout(timeout);
  }, [typingDone, isOtherSelected]);

  const handleSelect = (option: string) => {
    setSelected(option);
    setErrorMsg(null);

    if (otherOption && option === otherOption) {
      return;
    }

    setIsAdvancing(true);
    onSelect(option);
  };

  const handleOtherChange = (value: string) => {
    setOtherValue(value);
    onOtherValueChange?.(value);
    if (errorMsg) {
      setErrorMsg(null);
    }
  };

  const handleOtherContinue = () => {
    if (!otherOption) {
      return;
    }
    const trimmed = otherValue.trim();
    const validationError = validateHumanText(trimmed);
    if (validationError) {
      setErrorMsg(validationError);
      return;
    }
    setErrorMsg(null);
    setIsAdvancing(true);
    onSelect(otherOption, trimmed);
  };

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
          className="max-w-2xl space-y-5"
        >
          <div className="grid gap-3 sm:grid-cols-2">
            {options.map((option) => (
              <button
                key={option}
                type="button"
                disabled={isAdvancing}
                onClick={() => handleSelect(option)}
              className={`flex min-h-[60px] items-center rounded-lg border px-4 py-3 text-left text-base font-medium transition-all duration-200 ${
                selected === option
                    ? "border-blue-700 bg-blue-700 text-white"
                    : isAdvancing
                      ? "border-slate-200 text-slate-400"
                      : "border-slate-200 bg-white text-slate-700 hover:border-blue-400 hover:bg-blue-50 hover:text-blue-800"
                }`}
              >
                {option}
              </button>
            ))}
          </div>
          {isOtherSelected ? (
            <div className="max-w-2xl space-y-4 border-l-2 border-blue-600 bg-blue-50/60 p-5">
              <label className="block space-y-2">
                <span className="text-sm font-medium text-slate-600">Please specify</span>
                <input
                  ref={inputRef}
                  type="text"
                  value={otherValue}
                  placeholder="Type your answer"
                  onChange={(event) => handleOtherChange(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      event.preventDefault();
                      handleOtherContinue();
                    }
                  }}
                  className={`mt-3 ${INPUT_CLASSNAME}`}
                />
              </label>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                {errorMsg ? (
                  <p className="text-sm font-medium text-rose-500">{errorMsg}</p>
                ) : (
                  <p className="text-sm text-slate-500">We will store both the selected option and your custom value.</p>
                )}
                <button
                  type="button"
                  onClick={handleOtherContinue}
                  disabled={isAdvancing || !otherValue.trim()}
                  className="rounded-md bg-blue-700 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-blue-800 active:translate-y-px disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  Continue
                </button>
              </div>
            </div>
          ) : null}
        </motion.div>
      ) : null}
    </div>
  );
}
