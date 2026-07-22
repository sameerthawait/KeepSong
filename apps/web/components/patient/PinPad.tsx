"use client";

import { useState } from "react";

interface PinPadProps {
  onVerify: (pin: string) => void;
  errorMsg?: string;
}

export default function PinPad({ onVerify, errorMsg }: PinPadProps) {
  const [pin, setPin] = useState("");

  const handleDigit = (digit: string) => {
    if (pin.length < 6) {
      setPin((prev) => prev + digit);
    }
  };

  const handleDelete = () => {
    setPin((prev) => prev.slice(0, -1));
  };

  const handleClear = () => {
    setPin("");
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (pin.length >= 4) {
      onVerify(pin);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] p-6 text-amber-950 font-sans">
      <div className="w-full max-w-md bg-amber-50 p-8 rounded-3xl border-4 border-amber-800/20 shadow-2xl space-y-8 text-center">
        <div>
          <h1 className="text-4xl font-extrabold text-amber-950 tracking-tight">Daily Check-In</h1>
          <p className="text-2xl text-amber-900/80 mt-2 font-medium">Please enter your PIN</p>
        </div>

        {/* PIN Dots display */}
        <div className="flex justify-center items-center gap-4 py-4 min-h-[64px] bg-amber-100/60 rounded-2xl border-2 border-amber-900/20">
          {[0, 1, 2, 3].map((idx) => (
            <span
              key={idx}
              className={`w-6 h-6 rounded-full border-2 border-amber-950 transition-all ${
                pin.length > idx ? "bg-amber-900 scale-110" : "bg-amber-50"
              }`}
            />
          ))}
        </div>

        {errorMsg && (
          <p className="text-xl font-bold text-rose-700 bg-rose-100 p-3 rounded-xl border border-rose-300">
            {errorMsg}
          </p>
        )}

        {/* Number Pad Grid */}
        <div className="grid grid-cols-3 gap-4 max-w-xs mx-auto">
          {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((num) => (
            <button
              key={num}
              type="button"
              onClick={() => handleDigit(num)}
              className="w-20 h-20 min-w-[64px] min-h-[64px] rounded-2xl bg-amber-200 hover:bg-amber-300 active:bg-amber-400 text-amber-950 font-extrabold text-3xl shadow-md border-2 border-amber-800/30 transition flex items-center justify-center mx-auto"
            >
              {num}
            </button>
          ))}

          <button
            type="button"
            onClick={handleClear}
            className="w-20 h-20 min-w-[64px] min-h-[64px] rounded-2xl bg-amber-100 hover:bg-amber-200 text-amber-900 font-bold text-xl border-2 border-amber-800/20 transition flex items-center justify-center mx-auto"
          >
            Clear
          </button>

          <button
            type="button"
            onClick={() => handleDigit("0")}
            className="w-20 h-20 min-w-[64px] min-h-[64px] rounded-2xl bg-amber-200 hover:bg-amber-300 active:bg-amber-400 text-amber-950 font-extrabold text-3xl shadow-md border-2 border-amber-800/30 transition flex items-center justify-center mx-auto"
          >
            0
          </button>

          <button
            type="button"
            onClick={handleDelete}
            className="w-20 h-20 min-w-[64px] min-h-[64px] rounded-2xl bg-amber-100 hover:bg-amber-200 text-amber-900 font-bold text-xl border-2 border-amber-800/20 transition flex items-center justify-center mx-auto"
          >
            ⌫
          </button>
        </div>

        <div>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={pin.length < 4}
            className="w-full py-5 min-h-[64px] rounded-2xl bg-emerald-700 hover:bg-emerald-800 active:bg-emerald-900 disabled:opacity-40 text-white font-extrabold text-2xl shadow-xl transition"
          >
            Start Check-In
          </button>
        </div>
      </div>
    </div>
  );
}
