"use client";

import { useState } from "react";
import { createPatient, addFamilyMember, addStoryPrompt, suggestPhotoCaption } from "../../lib/api";

interface PatientSetupFormProps {
  onPatientCreated: (patient: any) => void;
}

export default function PatientSetupForm({ onPatientCreated }: PatientSetupFormProps) {
  const [patientName, setPatientName] = useState("");
  const [pin, setPin] = useState("1234");
  const [saving, setSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");

  // Family members state
  const [familyMembers, setFamilyMembers] = useState<Array<{ name: string; relationship: string; photoUrl: string }>>([
    { name: "Sarah", relationship: "Daughter", photoUrl: "https://images.unsplash.com/photo-1544005313-94ddf0286df2" }
  ]);
  const [memberName, setMemberName] = useState("");
  const [memberRelation, setMemberRelation] = useState("");
  const [memberPhoto, setMemberPhoto] = useState("");

  // AI Photo Caption Suggestion state
  const [photoCaptionSuggestion, setPhotoCaptionSuggestion] = useState<string | null>(null);
  const [photoCaptionLabel, setPhotoCaptionLabel] = useState<string>("");
  const [suggestingCaption, setSuggestingCaption] = useState(false);
  const [approvedCaption, setApprovedCaption] = useState<string | null>(null);

  // Prompts state
  const [prompts, setPrompts] = useState<string[]>([
    "Tell me about a memory that makes you smile today.",
    "Tell me about your favorite childhood pet."
  ]);
  const [customPrompt, setCustomPrompt] = useState("");

  const handleAddMember = (e: React.FormEvent) => {
    e.preventDefault();
    if (!memberName.trim() || !memberRelation.trim()) return;
    setFamilyMembers([...familyMembers, { name: memberName, relationship: memberRelation, photoUrl: memberPhoto }]);
    setMemberName("");
    setMemberRelation("");
    setMemberPhoto("");
  };

  const handleAddPrompt = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customPrompt.trim()) return;
    setPrompts([...prompts, customPrompt.trim()]);
    setCustomPrompt("");
  };

  const handleSuggestPhotoCaption = async (mName: string, mRel: string, mPhoto: string) => {
    setSuggestingCaption(true);
    try {
      // Temporary ID for photo caption suggestion request
      const res = await suggestPhotoCaption(
        "00000000-0000-0000-0000-000000000000",
        mPhoto || "https://images.unsplash.com/photo-1544005313-94ddf0286df2",
        mName,
        mRel
      );
      setPhotoCaptionSuggestion(res.suggested_caption);
      setPhotoCaptionLabel(res.label);
    } catch (err: any) {
      console.error("Failed to suggest photo caption:", err);
    } finally {
      setSuggestingCaption(false);
    }
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientName.trim()) return;

    setSaving(true);
    setErrorMsg("");

    try {
      // 1. Create Patient in backend
      const newPatient = await createPatient(patientName.trim(), pin.trim());

      // 2. Add Family Members
      for (const m of familyMembers) {
        await addFamilyMember(newPatient.id, m.name, m.relationship, m.photoUrl || undefined);
      }

      // 3. Add Story Prompts
      for (let i = 0; i < prompts.length; i++) {
        await addStoryPrompt(newPatient.id, prompts[i], i + 1);
      }

      onPatientCreated(newPatient);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to create patient profile.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 bg-slate-900/80 p-8 rounded-2xl border border-slate-800 shadow-xl max-w-4xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold text-slate-100">Patient Profile Setup</h2>
        <p className="text-slate-400 text-lg mt-1">Configure family members, orientation photos, and story prompts.</p>
      </div>

      {errorMsg && <p className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-300 font-semibold text-lg">{errorMsg}</p>}

      <form onSubmit={handleSaveProfile} className="space-y-8">
        {/* Basic Information */}
        <div className="space-y-4">
          <h3 className="text-xl font-semibold text-amber-300">1. Basic Details</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-slate-300 text-base mb-1 font-medium">Patient Full Name</label>
              <input
                type="text"
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                placeholder="e.g. John Doe"
                className="w-full px-4 py-3 min-h-[48px] rounded-xl bg-slate-950 border border-slate-700 text-white placeholder-slate-500 text-lg focus:outline-none focus:border-amber-500"
                required
              />
            </div>
            <div>
              <label className="block text-slate-300 text-base mb-1 font-medium">Daily Check-In PIN (4-6 digits)</label>
              <input
                type="text"
                value={pin}
                onChange={(e) => setPin(e.target.value)}
                placeholder="1234"
                className="w-full px-4 py-3 min-h-[48px] rounded-xl bg-slate-950 border border-slate-700 text-white text-lg focus:outline-none focus:border-amber-500"
                required
              />
            </div>
          </div>
        </div>

        {/* Family Members & AI Photo Caption Suggestion */}
        <div className="space-y-4 border-t border-slate-800 pt-6">
          <h3 className="text-xl font-semibold text-amber-300">2. Family Members & Orientation Photos</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <input
              type="text"
              placeholder="Name (e.g. Sarah)"
              value={memberName}
              onChange={(e) => setMemberName(e.target.value)}
              className="px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white text-lg"
            />
            <input
              type="text"
              placeholder="Relationship (e.g. Daughter)"
              value={memberRelation}
              onChange={(e) => setMemberRelation(e.target.value)}
              className="px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white text-lg"
            />
            <button
              type="button"
              onClick={handleAddMember}
              className="px-4 py-3 min-h-[48px] bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl text-lg transition cursor-pointer"
            >
              + Add Relative
            </button>
          </div>

          <div className="space-y-3 mt-4">
            {familyMembers.map((m, idx) => (
              <div key={idx} className="p-4 bg-slate-950 border border-slate-700 rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <span className="w-10 h-10 rounded-full bg-[#2E5D4E] flex items-center justify-center font-bold text-white text-lg">
                    {m.name[0]}
                  </span>
                  <div>
                    <p className="text-white font-semibold text-lg">{m.name}</p>
                    <p className="text-slate-400 text-base">{m.relationship}</p>
                    {approvedCaption && <p className="text-amber-300 text-sm italic mt-1">"{approvedCaption}"</p>}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleSuggestPhotoCaption(m.name, m.relationship, m.photoUrl)}
                  disabled={suggestingCaption}
                  className="px-4 py-2 bg-indigo-600/80 hover:bg-indigo-600 text-white text-sm font-semibold rounded-lg shadow-sm cursor-pointer"
                >
                  {suggestingCaption ? "Generating..." : "Generate AI Photo Caption 🪄"}
                </button>
              </div>
            ))}
          </div>

          {/* AI Photo Caption Approval Review Step */}
          {photoCaptionSuggestion && (
            <div className="p-5 bg-amber-950/40 rounded-xl border-2 border-amber-500/40 space-y-3 mt-4">
              <div className="flex items-center justify-between">
                <span className="text-amber-300 font-bold text-base">Suggested Photo Caption</span>
                <span className="px-3 py-1 bg-[#2E5D4E] text-white rounded-full text-xs font-bold uppercase">
                  {photoCaptionLabel || "AI suggestion — please review"}
                </span>
              </div>
              <p className="text-slate-100 text-lg italic font-medium">"{photoCaptionSuggestion}"</p>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setApprovedCaption(photoCaptionSuggestion);
                    setPhotoCaptionSuggestion(null);
                  }}
                  className="px-4 py-2 bg-[#3A7D5C] hover:bg-[#2E5D4E] text-white font-bold text-sm rounded-lg transition cursor-pointer"
                >
                  Approve Caption ✓
                </button>
                <button
                  type="button"
                  onClick={() => setPhotoCaptionSuggestion(null)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium rounded-lg"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Story Prompts */}
        <div className="space-y-4 border-t border-slate-800 pt-6">
          <h3 className="text-xl font-semibold text-amber-300">3. Sequenced Daily Story Prompts</h3>
          
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Write a custom memory prompt..."
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              className="flex-1 px-4 py-3 rounded-xl bg-slate-950 border border-slate-700 text-white text-lg"
            />
            <button
              type="button"
              onClick={handleAddPrompt}
              className="px-6 py-3 min-h-[48px] bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl text-lg cursor-pointer"
            >
              + Add Prompt
            </button>
          </div>

          <ul className="space-y-2 mt-4">
            {prompts.map((p, idx) => (
              <li key={idx} className="p-4 bg-slate-950 border border-slate-800 rounded-xl text-slate-200 text-lg flex items-center gap-3">
                <span className="text-amber-400 font-bold">#{idx + 1}</span>
                <span>{p}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="pt-6 border-t border-slate-800">
          <button
            type="submit"
            disabled={saving || !patientName.trim()}
            className="w-full py-4 min-h-[52px] rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-xl shadow-lg shadow-indigo-600/30 transition cursor-pointer"
          >
            {saving ? "Creating Profile..." : "Create Patient Profile & Setup Prompt Queue"}
          </button>
        </div>
      </form>
    </div>
  );
}
