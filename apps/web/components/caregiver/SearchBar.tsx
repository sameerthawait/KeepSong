"use client";

import { useState } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  onClear: () => void;
}

export default function SearchBar({ onSearch, onClear }: SearchBarProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    onSearch(query.trim());
  };

  const handleReset = () => {
    setQuery("");
    onClear();
  };

  return (
    <form onSubmit={handleSubmit} className="relative flex items-center gap-3 w-full max-w-3xl mx-auto">
      <div className="relative flex-1">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Semantic search e.g. 'stories about her dog' or 'first job'..."
          className="w-full px-5 py-4 pl-12 rounded-2xl bg-slate-900 border-2 border-slate-700 focus:border-amber-500 text-white placeholder-slate-400 text-lg shadow-inner focus:outline-none transition"
        />
        <span className="absolute left-4 top-4 text-xl text-slate-400">🔍</span>
      </div>

      <button
        type="submit"
        className="px-6 py-4 min-h-[56px] rounded-2xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-lg shadow-lg shadow-amber-500/20 transition"
      >
        Search
      </button>

      {query && (
        <button
          type="button"
          onClick={handleReset}
          className="px-4 py-4 min-h-[56px] rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-lg transition"
        >
          Reset
        </button>
      )}
    </form>
  );
}
