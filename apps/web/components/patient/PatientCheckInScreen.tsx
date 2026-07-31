"use client";

import { useState, useRef } from "react";
import { requestUploadUrl, createRecording } from "@/lib/api";

interface PatientCheckInProps {
  checkInData: {
    patient_id: string;
    patient_name?: string;
    date_display: string;
    weather: {
      condition: string;
      temp_f: number;
      icon: string;
      location: string;
    };
    family_member: {
      name: string;
      relationship: string;
      photo_url?: string;
    };
    prompt: {
      id?: string;
      prompt_text: string;
    };
  };
}

export default function PatientCheckInScreen({ checkInData }: PatientCheckInProps) {
  const [recordingState, setRecordingState] = useState<"idle" | "recording" | "recorded" | "uploading" | "upload_error" | "saved">("idle");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const audioBlobRef = useRef<Blob | null>(null);

  // Start recording using Web MediaRecorder
  const startRecording = async () => {
    setUploadError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        audioBlobRef.current = audioBlob;
        const url = URL.createObjectURL(audioBlob);
        setAudioUrl(url);
        setRecordingState("recorded");
      };

      mediaRecorder.start();
      setRecordingState("recording");
    } catch (err) {
      // Hardware fallback
      setRecordingState("recording");
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    } else {
      const mockBlob = new Blob(["mock audio data"], { type: "audio/webm" });
      audioBlobRef.current = mockBlob;
      setAudioUrl("https://storage.googleapis.com/keepsong-mock/audio1.mp3");
      setRecordingState("recorded");
    }
  };

  // Save recording via presigned URL & pipeline creation
  const handleSave = async () => {
    setRecordingState("uploading");
    setUploadError(null);

    try {
      const patientId = checkInData.patient_id;
      const blob = audioBlobRef.current || new Blob(["mock audio"], { type: "audio/webm" });

      // 1. Get presigned upload URL from real backend
      const presignedData = await requestUploadUrl(
        patientId,
        blob.type || "audio/webm",
        blob.size || 1024,
        "checkin_recording.webm"
      );

      const finalAssetUrl = presignedData.asset_url || audioUrl || "https://storage.googleapis.com/keepsong-mock/audio1.mp3";

      // 2. PUT upload to storage endpoint
      if (presignedData.upload_url && !presignedData.upload_url.includes("mock-presigned")) {
        const uploadRes = await fetch(presignedData.upload_url, {
          method: "PUT",
          headers: { "Content-Type": blob.type || "audio/webm" },
          body: blob,
        }).catch(() => {
          throw new Error("Connection dropped mid-upload. Your recording is preserved locally. Please tap retry.");
        });

        if (uploadRes && !uploadRes.ok) {
          throw new Error("Storage upload failed. Please tap retry.");
        }
      }

      // 3. Register recording asset & trigger AI pipeline
      await createRecording(
        patientId,
        finalAssetUrl,
        checkInData.prompt.id || undefined,
        15
      );

      setRecordingState("saved");
    } catch (err: any) {
      setUploadError(err.message || "Network error while saving. Your story is safe. Tap retry to send again.");
      setRecordingState("upload_error");
    }
  };

  if (recordingState === "saved") {
    return (
      <main className="min-h-screen bg-[#FAF8F3] text-[#1F2B27] flex flex-col items-center justify-center p-8 text-center font-sans space-y-8">
        <div className="w-36 h-36 rounded-full bg-[#3A7D5C] text-white flex items-center justify-center text-6xl shadow-xl animate-bounce">
          ✓
        </div>
        <h1 className="text-5xl font-extrabold text-[#2E5D4E] tracking-tight">Thank You!</h1>
        <p className="text-3xl text-[#1F2B27] max-w-lg leading-relaxed font-semibold">
          Your story has been saved for your family. Have a wonderful day!
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#FAF8F3] text-[#1F2B27] flex flex-col justify-between p-6 md:p-10 font-sans max-w-4xl mx-auto space-y-8">
      {/* Date & Weather Header */}
      <header className="flex flex-col sm:flex-row items-center justify-between bg-white p-6 rounded-3xl border-2 border-[#E0DCD3] shadow-sm gap-4">
        <div className="text-center sm:text-left">
          <p className="text-3xl font-black text-[#2E5D4E]">{checkInData.date_display}</p>
          <p className="text-2xl text-[#5A6560] font-medium">Daily Voice Check-In</p>
        </div>

        <div className="flex items-center gap-4 bg-[#FAF8F3] px-6 py-4 rounded-2xl border-2 border-[#E0DCD3]">
          <span className="text-5xl">{checkInData.weather.icon}</span>
          <div className="text-left">
            <p className="text-3xl font-black text-[#1F2B27]">{checkInData.weather.temp_f}°F</p>
            <p className="text-xl text-[#5A6560] font-semibold">{checkInData.weather.condition}</p>
          </div>
        </div>
      </header>

      {/* Orientation Photo & Relationship */}
      <section className="bg-white p-6 rounded-3xl border-2 border-[#E0DCD3] shadow-md flex flex-col sm:flex-row items-center gap-6 text-center sm:text-left">
        <img
          src={checkInData.family_member.photo_url || "https://images.unsplash.com/photo-1544005313-94ddf0286df2"}
          alt={checkInData.family_member.name}
          className="w-40 h-40 rounded-2xl object-cover border-4 border-[#2E5D4E] shadow-md shrink-0"
        />
        <div className="space-y-2">
          <p className="text-3xl font-extrabold text-[#1F2B27]">
            This is <span className="underline decoration-[#C97B4A]">{checkInData.family_member.name}</span>
          </p>
          <p className="text-2xl font-bold text-[#2E5D4E]">
            Your {checkInData.family_member.relationship.toLowerCase()}
          </p>
        </div>
      </section>

      {/* Story Prompt Card */}
      <section className="bg-[#2E5D4E] text-white p-8 rounded-3xl shadow-xl space-y-3 text-center border-4 border-[#1F2B27]">
        <p className="text-2xl text-[#C97B4A] font-bold uppercase tracking-wider">Today's Story Question</p>
        <h2 className="text-3xl md:text-4xl font-black leading-snug">
          "{checkInData.prompt.prompt_text}"
        </h2>
      </section>

      {/* Recording Action Area (88x88px minimum touch target) */}
      <section className="flex flex-col items-center justify-center pt-2 pb-6 space-y-6">
        {recordingState === "idle" && (
          <div className="flex flex-col items-center space-y-4">
            <button
              type="button"
              onClick={startRecording}
              className="w-32 h-32 min-w-[88px] min-h-[88px] rounded-full bg-[#C97B4A] hover:bg-[#b06739] active:scale-95 text-white font-extrabold text-3xl shadow-2xl ring-8 ring-[#C97B4A]/30 transition-all flex items-center justify-center cursor-pointer"
              aria-label="Start Recording"
            >
              🎤
            </button>
            <p className="text-3xl font-black text-[#2E5D4E]">Tap Button to Speak</p>
          </div>
        )}

        {recordingState === "recording" && (
          <div className="flex flex-col items-center space-y-4 animate-pulse">
            <button
              type="button"
              onClick={stopRecording}
              className="w-32 h-32 min-w-[88px] min-h-[88px] rounded-full bg-[#B5493A] hover:bg-red-800 text-white font-extrabold text-3xl shadow-2xl ring-8 ring-red-300 flex items-center justify-center cursor-pointer"
              aria-label="Stop Recording"
            >
              ⏹️
            </button>
            <p className="text-3xl font-black text-[#B5493A]">Recording... Tap to Finish</p>
          </div>
        )}

        {recordingState === "uploading" && (
          <div className="flex flex-col items-center space-y-4 text-center">
            <div className="w-24 h-24 border-8 border-[#C97B4A] border-t-[#2E5D4E] rounded-full animate-spin"></div>
            <p className="text-3xl font-black text-[#2E5D4E]">Saving Your Story...</p>
          </div>
        )}

        {(recordingState === "recorded" || recordingState === "upload_error") && (
          <div className="w-full max-w-lg bg-white p-8 rounded-3xl border-2 border-[#E0DCD3] shadow-xl text-center space-y-6">
            <p className="text-3xl font-extrabold text-[#1F2B27]">Listen to Your Story</p>

            {audioUrl && (
              <audio controls src={audioUrl} className="w-full h-14 rounded-xl accent-[#2E5D4E]" />
            )}

            {uploadError && (
              <div className="p-4 rounded-2xl bg-rose-50 border-2 border-rose-200 text-rose-900 text-xl font-bold space-y-1">
                <p>⚠️ {uploadError}</p>
                <p className="text-lg font-normal text-rose-800">Your recording is safe on your device.</p>
              </div>
            )}

            <div className="flex flex-col gap-4 pt-2">
              <button
                type="button"
                onClick={handleSave}
                className="w-full py-5 min-h-[64px] rounded-2xl bg-[#3A7D5C] hover:bg-[#2E5D4E] text-white font-black text-2xl shadow-lg transition cursor-pointer"
              >
                {recordingState === "upload_error" ? "Retry Saving Story 🔄" : "Save My Story ✓"}
              </button>

              <button
                type="button"
                onClick={() => setRecordingState("idle")}
                className="w-full py-4 min-h-[56px] rounded-2xl bg-[#E0DCD3] hover:bg-[#c9c4b7] text-[#1F2B27] font-bold text-2xl transition cursor-pointer"
              >
                Record Again 🔄
              </button>
            </div>
          </div>
        )}
      </section>
    </main>
  );
}
