"use client";

import { useState } from "react";
import PinPad from "@/components/patient/PinPad";
import PatientCheckInScreen from "@/components/patient/PatientCheckInScreen";

export default function PatientCheckInPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Default check-in data matching spec requirements
  const mockCheckInData = {
    date_display: "Wednesday, July 22, 2026",
    weather: {
      condition: "Partly Cloudy",
      temp_f: 72,
      icon: "⛅",
      location: "Springfield"
    },
    family_member: {
      name: "Sarah",
      relationship: "Daughter",
      photo_url: "https://images.unsplash.com/photo-1544005313-94ddf0286df2"
    },
    prompt: {
      id: "prompt-1",
      prompt_text: "Tell me about your favorite childhood pet."
    }
  };

  const handleVerifyPin = (pin: string) => {
    if (pin === "1234") {
      setIsAuthenticated(true);
      setErrorMsg("");
    } else {
      setErrorMsg("Incorrect PIN. Please try again.");
    }
  };

  if (!isAuthenticated) {
    return <PinPad onVerify={handleVerifyPin} errorMsg={errorMsg} />;
  }

  return <PatientCheckInScreen checkInData={mockCheckInData} />;
}
