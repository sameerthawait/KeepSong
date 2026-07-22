"use client";

import { useState } from "react";

interface PatientSetupFormProps {
  onPatientCreated: (patient: any) => void;
}

export default function PatientSetupForm({ onPatientCreated }: PatientSetupFormProps) {
  const [patientName, setPatientName] = useState("");
  const [pin, setPin] = useState("1234");
  
  // Family members state
  const [familyMembers, setFamilyMembers] = useState<Array<{ name: string; relationship: string; photoUrl: string }>>([
    { name: "Jane Doe", relationship: "Daughter", photoUrl: "" }
  ]);
  const [memberName, setMemberName] = useState("");
  const [memberRelation, setMemberRelation] = useState("");
  const [memberPhoto, setMemberPhoto] = useState("");

  // Prompts state
  const [prompts, setPrompts] = useState<string[]>([
    "Tell me about your favorite childhood pet.",
    "What was your first job, and what did you like about it?"
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

  const handleSaveProfile = (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientName.trim()) return;

    const mockPatient = {
      id: "mock-patient-123",
      name: patientName,
      has_consent: false,
      familyMembers,
      prompts
    };

    onPatientCreated(mockPatient);
  };

  return (
    <div className="space-y-8 bg-slate-900/80 p-8 rounded-2xl border border-slate-800 shadow-xl max-w-4xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold text-slate-100">Patient Profile Setup</h2>
        <p className="text-slate-400 text-lg mt-1">Configure family members, orientation photos, and story prompts.</p>
      </div>

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

        {/* Family Members */}
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
              className="px-4 py-3 min-h-[48px] bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl text-lg transition"
            >
              + Add Relative
            </button>
          </div>

          <div className="flex flex-wrap gap-3 mt-4">
            {familyMembers.map((m, idx) => (
              <div key={idx} className="px-4 py-3 bg-slate-950 border border-slate-700 rounded-xl flex items-center gap-3">
                <span className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-white">
                  {m.name[0]}
                </span>
                <div>
                  <p className="text-white font-semibold text-base">{m.name}</p>
                  <p className="text-slate-400 text-sm">{m.relationship}</p>
                </div>
              </div>
            ))}
          </div>
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
              className="px-6 py-3 min-h-[48px] bg-slate-800 hover:bg-slate-700 text-white font-semibold rounded-xl text-lg"
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
            className="w-full py-4 min-h-[52px] rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xl shadow-lg shadow-indigo-600/30 transition"
          >
            Create Patient Profile & Setup Prompt Queue
          </button>
        </div>
      </form>
    </div>
  );
}
