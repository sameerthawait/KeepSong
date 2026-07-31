"use client";

import { useState } from "react";

interface PinPadProps {
  onVerify: (pin: string) => void;
  errorMsg?: string;
  isVerifying?: boolean;
}

export default function PinPad({ onVerify, errorMsg, isVerifying = false }: PinPadProps) {
  const [pin, setPin] = useState("");

  const handleDigit = (digit: string) => {
    if (pin.length < 6) {
      const nextPin = pin + digit;
      setPin(nextPin);
      if (nextPin.length >= 4) {
        onVerify(nextPin);
      }
    }
  };

  const handleStartOver = () => {
    setPin("");
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[85vh] p-6 bg-[#FAF8F3] text-[#1F2B27] font-sans">
      <div className="w-full max-w-lg bg-white p-10 rounded-3xl border-2 border-[#E0DCD3] shadow-xl space-y-8 text-center">
        <div>
          <h1 className="text-4xl font-extrabold text-[#2E5D4E] tracking-tight">Daily Check-In</h1>
          <p className="text-2xl text-[#5A6560] mt-3 font-medium">Please tap your PIN to begin</p>
        </div>

        {/* PIN Indicator Dots */}
        <div className="flex justify-center items-center gap-4 py-4 min-h-[72px] bg-[#FAF8F3] rounded-2xl border-2 border-[#E0DCD3]">
          {[0, 1, 2, 3].map((idx) => (
            <span
              key={idx}
              className={`w-7 h-7 rounded-full border-2 border-[#2E5D4E] transition-all ${
                pin.length > idx ? "bg-[#2E5D4E] scale-110" : "bg-white"
              }`}
            />
          ))}
        </div>

        {errorMsg && (
          <div className="p-4 rounded-2xl bg-rose-50 border-2 border-rose-200 text-rose-800 text-xl font-bold">
            ⚠️ {errorMsg}
          </div>
        )}

        {/* 64x64px Minimum Keypad Grid */}
        <div className="grid grid-cols-3 gap-5 max-w-xs mx-auto">
          {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((num) => (
            <button
              key={num}
              type="button"
              disabled={isVerifying}
              onClick={() => handleDigit(num)}
              className="w-20 h-20 min-w-[64px] min-h-[64px] rounded-2xl bg-[#FAF8F3] hover:bg-[#E0DCD3] active:bg-[#2E5D4E] active:text-white text-[#2E5D4E] font-black text-3xl shadow-sm border-2 border-[#E0DCD3] transition flex items-center justify-center mx-auto cursor-pointer"
            >
              {num}
            </button>
          ))}

          <div className="w-20 h-20" />

          <button
            type="button"
            disabled={isVerifying}
            onClick={() => handleDigit("0")}
            className="w-20 h-20 min-w-[64px] min-h-[64px] rounded-2xl bg-[#FAF8F3] hover:bg-[#E0DCD3] active:bg-[#2E5D4E] active:text-white text-[#2E5D4E] font-black text-3xl shadow-sm border-2 border-[#E0DCD3] transition flex items-center justify-center mx-auto cursor-pointer"
          >
            0
          </button>

          <div className="w-20 h-20" />
        </div>

        {/* Single Obvious Start Over Affordance */}
        <div className="pt-2">
          <button
            type="button"
            onClick={handleStartOver}
            className="w-full py-4 min-h-[64px] rounded-2xl bg-[#E0DCD3] hover:bg-[#c9c4b7] text-[#1F2B27] font-bold text-2xl transition"
          >
            Start Over 🔄
          </button>
        </div>
      </div>
    </div>
  );
}
