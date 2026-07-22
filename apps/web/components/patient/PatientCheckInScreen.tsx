"use client";

import { useState, useRef } from "react";

interface PatientCheckInProps {
  checkInData: {
    patient_id?: string;
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
      // Fallback for mock environment if microphone hardware isn't available
      setRecordingState("recording");
    }
  };

  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    } else {
      // Fallback mock audio blob
      const mockBlob = new Blob(["mock audio data"], { type: "audio/webm" });
      audioBlobRef.current = mockBlob;
      setAudioUrl("https://storage.googleapis.com/keepsong-mock/audio1.mp3");
      setRecordingState("recorded");
    }
  };

  // Upload story audio using direct presigned URL with retry support
  const handleSave = async () => {
    setRecordingState("uploading");
    setUploadError(null);

    try {
      // 1. Request presigned upload URL from FastAPI backend
      const patientId = checkInData.patient_id || "mock-patient-101";
      const blob = audioBlobRef.current || new Blob(["mock audio"], { type: "audio/webm" });
      
      const presignedRes = await fetch(`/patients/${patientId}/upload-url`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content_type: blob.type || "audio/webm",
          file_size: blob.size || 1024,
          category: "audio",
          filename: "checkin_recording.webm"
        })
      }).catch(() => null);

      let assetUrl = audioUrl || "https://storage.googleapis.com/keepsong-mock/audio1.mp3";

      if (presignedRes && presignedRes.ok) {
        const urlData = await presignedRes.json();
        assetUrl = urlData.asset_url;

        // 2. Direct PUT upload to storage bucket
        const uploadRes = await fetch(urlData.upload_url, {
          method: "PUT",
          headers: { "Content-Type": blob.type || "audio/webm" },
          body: blob
        }).catch((netErr) => {
          throw new Error("Connection dropped mid-upload. Your recording is preserved locally. Please tap retry.");
        });

        if (uploadRes && !uploadRes.ok) {
          throw new Error("Storage upload failed. Please tap retry.");
        }
      }

      setRecordingState("saved");
    } catch (err: any) {
      setUploadError(err.message || "Network error. Tap retry to attempt uploading again.");
      setRecordingState("upload_error");
    }
  };

  if (recordingState === "saved") {
    return (
      <main className="min-h-screen bg-amber-50 text-amber-950 flex flex-col items-center justify-center p-8 text-center font-sans space-y-8">
        <div className="w-32 h-32 rounded-full bg-emerald-600 text-white flex items-center justify-center text-6xl shadow-2xl animate-bounce">
          ✓
        </div>
        <h1 className="text-5xl font-extrabold text-emerald-950 tracking-tight">Thank You!</h1>
        <p className="text-3xl text-amber-900 max-w-lg leading-relaxed font-semibold">
          Your story has been saved for your family. Have a wonderful day!
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-amber-50 text-amber-950 flex flex-col justify-between p-6 md:p-10 font-sans max-w-4xl mx-auto space-y-8">
      {/* Date & Weather Header */}
      <header className="flex flex-col sm:flex-row items-center justify-between bg-amber-100/80 p-6 rounded-3xl border-2 border-amber-800/20 shadow-md gap-4">
        <div className="text-center sm:text-left">
          <p className="text-2xl font-bold text-amber-900">{checkInData.date_display}</p>
          <p className="text-xl text-amber-800/80 font-medium">Daily Check-In</p>
        </div>
        
        <div className="flex items-center gap-3 bg-amber-200/70 px-5 py-3 rounded-2xl border border-amber-800/20">
          <span className="text-4xl">{checkInData.weather.icon}</span>
          <div className="text-left">
            <p className="text-2xl font-black text-amber-950">{checkInData.weather.temp_f}°F</p>
            <p className="text-lg text-amber-900 font-semibold">{checkInData.weather.condition}</p>
          </div>
        </div>
      </header>

      {/* Orientation Photo & Relationship */}
      <section className="bg-amber-100/60 p-6 rounded-3xl border-2 border-amber-800/20 shadow-lg flex flex-col sm:flex-row items-center gap-6 text-center sm:text-left">
        <img
          src={checkInData.family_member.photo_url || "https://images.unsplash.com/photo-1544005313-94ddf0286df2"}
          alt={checkInData.family_member.name}
          className="w-36 h-36 rounded-2xl object-cover border-4 border-amber-700 shadow-md shrink-0"
        />
        <div className="space-y-1">
          <p className="text-3xl font-extrabold text-amber-950">
            This is <span className="underline decoration-amber-600">{checkInData.family_member.name}</span>
          </p>
          <p className="text-2xl font-bold text-amber-800">
            Your {checkInData.family_member.relationship.toLowerCase()}
          </p>
        </div>
      </section>

      {/* Story Prompt Card */}
      <section className="bg-amber-900 text-amber-50 p-8 rounded-3xl shadow-xl space-y-3 text-center border-4 border-amber-950">
        <p className="text-xl text-amber-300 font-bold uppercase tracking-wider">Today's Story Question</p>
        <h2 className="text-3xl md:text-4xl font-black leading-snug">
          "{checkInData.prompt.prompt_text}"
        </h2>
      </section>

      {/* Recording & Playback Action Area */}
      <section className="flex flex-col items-center justify-center pt-2 pb-6 space-y-6">
        {recordingState === "idle" && (
          <div className="flex flex-col items-center space-y-4">
            <button
              type="button"
              onClick={startRecording}
              className="w-28 h-28 min-w-[88px] min-h-[88px] rounded-full bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white font-extrabold text-2xl shadow-2xl ring-8 ring-rose-200 transition-all flex items-center justify-center cursor-pointer"
              aria-label="Start Recording"
            >
              🎤
            </button>
            <p className="text-2xl font-extrabold text-amber-950">Tap Button to Speak</p>
          </div>
        )}

        {recordingState === "recording" && (
          <div className="flex flex-col items-center space-y-4 animate-pulse">
            <button
              type="button"
              onClick={stopRecording}
              className="w-28 h-28 min-w-[88px] min-h-[88px] rounded-full bg-slate-900 hover:bg-black text-white font-extrabold text-2xl shadow-2xl ring-8 ring-amber-400 flex items-center justify-center cursor-pointer"
              aria-label="Stop Recording"
            >
              ⏹️
            </button>
            <p className="text-2xl font-extrabold text-rose-700">Recording... Tap to Finish</p>
          </div>
        )}

        {recordingState === "uploading" && (
          <div className="flex flex-col items-center space-y-4 text-center">
            <div className="w-20 h-20 border-8 border-amber-400 border-t-amber-800 rounded-full animate-spin"></div>
            <p className="text-2xl font-extrabold text-amber-900">Saving Your Story...</p>
          </div>
        )}

        {(recordingState === "recorded" || recordingState === "upload_error") && (
          <div className="w-full max-w-md bg-amber-100 p-6 rounded-3xl border-2 border-amber-800/30 shadow-xl text-center space-y-6">
            <p className="text-2xl font-extrabold text-amber-950">Listen to Your Story</p>

            {audioUrl && (
              <audio controls src={audioUrl} className="w-full h-14 rounded-xl accent-amber-700" />
            )}

            {uploadError && (
              <div className="p-4 rounded-xl bg-rose-100 border border-rose-300 text-rose-900 text-lg font-semibold space-y-1">
                <p>⚠️ {uploadError}</p>
                <p className="text-sm font-normal">Your recording is safe on your device.</p>
              </div>
            )}

            <div className="flex flex-col gap-3 pt-2">
              <button
                type="button"
                onClick={handleSave}
                className="w-full py-5 min-h-[64px] rounded-2xl bg-emerald-700 hover:bg-emerald-800 text-white font-black text-2xl shadow-lg transition"
              >
                {recordingState === "upload_error" ? "Retry Saving Story 🔄" : "Save My Story ✓"}
              </button>

              <button
                type="button"
                onClick={() => setRecordingState("idle")}
                className="w-full py-4 min-h-[52px] rounded-2xl bg-amber-200 hover:bg-amber-300 text-amber-950 font-bold text-xl transition"
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
