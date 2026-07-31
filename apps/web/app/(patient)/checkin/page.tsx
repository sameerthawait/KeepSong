"use client";

import { useState, useEffect } from "react";
import PinPad from "@/components/patient/PinPad";
import PatientCheckInScreen from "@/components/patient/PatientCheckInScreen";
import { verifyPatientPin, getPatientCheckIn, listPatients } from "@/lib/api";

export default function PatientCheckInPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [patientId, setPatientId] = useState<string | null>(null);
  const [checkInData, setCheckInData] = useState<any>(null);

  // Auto-discover target patient ID from backend on load
  useEffect(() => {
    async function loadDefaultPatient() {
      try {
        const patients = await listPatients();
        if (patients && patients.length > 0) {
          setPatientId(patients[0].id);
        }
      } catch (err) {
        // Default fallback patient ID
        setPatientId("11111111-1111-1111-1111-111111111111");
      }
    }
    loadDefaultPatient();
  }, []);

  const handleVerifyPin = async (pin: string) => {
    const targetId = patientId || "11111111-1111-1111-1111-111111111111";
    setIsVerifying(true);
    setErrorMsg("");

    try {
      // 1. Call real verify-pin endpoint
      await verifyPatientPin(targetId, pin);

      // 2. Fetch real checkin data
      const checkin = await getPatientCheckIn(targetId);
      setCheckInData(checkin);
      setIsAuthenticated(true);
    } catch (err: any) {
      setErrorMsg(err.message || "Incorrect PIN. Please try again.");
    } finally {
      setIsVerifying(false);
    }
  };

  if (!isAuthenticated) {
    return <PinPad onVerify={handleVerifyPin} errorMsg={errorMsg} isVerifying={isVerifying} />;
  }

  return <PatientCheckInScreen checkInData={checkInData} />;
}
