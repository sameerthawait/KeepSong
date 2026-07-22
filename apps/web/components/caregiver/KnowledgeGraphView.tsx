"use client";

export interface GraphEntity {
  id: string;
  patient_id: string;
  type: "person" | "place" | "event" | string;
  name: string;
}

export interface GraphRelationship {
  id: string;
  entity_id_a: string;
  entity_id_b: string;
  relationship_type: string;
}

interface KnowledgeGraphViewProps {
  entities: GraphEntity[];
  relationships: GraphRelationship[];
}

export default function KnowledgeGraphView({ entities, relationships }: KnowledgeGraphViewProps) {
  if (entities.length === 0) {
    return (
      <div className="p-8 text-center bg-slate-900/50 rounded-2xl border border-slate-800 text-slate-400 text-lg max-w-3xl mx-auto">
        No story entities extracted yet. As check-ins are recorded, people, places, and events will populate this graph.
      </div>
    );
  }

  const getTypeBadge = (type: string) => {
    switch (type.toLowerCase()) {
      case "person":
        return "bg-indigo-500/20 text-indigo-300 border-indigo-500/40";
      case "place":
        return "bg-emerald-500/20 text-emerald-300 border-emerald-500/40";
      case "event":
        return "bg-amber-500/20 text-amber-300 border-amber-500/40";
      default:
        return "bg-slate-700 text-slate-300 border-slate-600";
    }
  };

  return (
    <div className="p-8 rounded-2xl bg-slate-900 border border-slate-800 space-y-8 max-w-5xl mx-auto shadow-xl">
      <div>
        <h3 className="text-2xl font-bold text-slate-100">Life Story Knowledge Graph</h3>
        <p className="text-slate-400 text-lg mt-1">Extracted people, places, and historical events linked across check-in stories.</p>
      </div>

      {/* Entity Nodes Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
        {entities.map((entity) => (
          <div
            key={entity.id}
            className="p-5 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between hover:border-amber-500/40 transition shadow-md"
          >
            <div>
              <p className="text-xl font-bold text-slate-100">{entity.name}</p>
              <span className={`inline-block mt-2 px-3 py-1 text-xs font-semibold uppercase tracking-wider rounded-full border ${getTypeBadge(entity.type)}`}>
                {entity.type}
              </span>
            </div>
            <span className="text-3xl">
              {entity.type === "person" ? "👤" : entity.type === "place" ? "📍" : "📅"}
            </span>
          </div>
        ))}
      </div>

      {/* Graph Relationships List */}
      {relationships.length > 0 && (
        <div className="space-y-4 pt-4 border-t border-slate-800">
          <h4 className="text-xl font-semibold text-amber-300">Extracted Graph Connections</h4>
          <div className="space-y-3">
            {relationships.map((rel) => {
              const entityA = entities.find((e) => e.id === rel.entity_id_a)?.name || "Entity A";
              const entityB = entities.find((e) => e.id === rel.entity_id_b)?.name || "Entity B";
              return (
                <div
                  key={rel.id}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between font-mono text-base text-slate-300"
                >
                  <span className="font-bold text-indigo-300">{entityA}</span>
                  <span className="px-3 py-1 rounded-full bg-slate-800 text-amber-400 text-xs font-semibold uppercase">
                    ── {rel.relationship_type} ──►
                  </span>
                  <span className="font-bold text-amber-300">{entityB}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
