import { useEffect, useState } from "react";

export function useTypewriter(text: string, speed: number = 28) {
  const [typingState, setTypingState] = useState({ source: text, index: 0 });

  useEffect(() => {
    let index = 0;
    const interval = window.setInterval(() => {
      index += 1;
      setTypingState({ source: text, index });
      if (index >= text.length) {
        window.clearInterval(interval);
      }
    }, speed);

    return () => {
      window.clearInterval(interval);
    };
  }, [text, speed]);

  if (typingState.source !== text) {
    return "";
  }

  return text.slice(0, typingState.index);
}
