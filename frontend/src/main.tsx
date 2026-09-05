import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Brief = {
  id: string;
  account: string;
  owner: string;
  region: string;
  segment: string;
  regulator: string;
  problem: string;
  systems: string[];
  expected_timeline: string;
  success_criteria: string[];
  received_at: string;
};
type Match = {
  template: {
    id: string;
    name: string;
    region: string;
    segment: string;
    outcome: string;
    document_path?: string;
  };
  score: number;
  reasons: string[];
};
type Analysis = {
  template_id: string;
  recommendation: string;
  match_reasons: string[];
  mismatches: string[];
  required_changes: string[];
};
type Draft = {
  template_analysis: Analysis[];
  recommended_templates: any[];
  poc_plan: any;
  delivery_handoff: any;
  open_questions: string[];
};
type Item = {
  brief: Brief;
  health: any;
  draft?: { draft: Draft; matches: Match[]; provider: string };
  trigger?: any;
};
const API = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
async function request(path: string, init?: RequestInit) {
  const r = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  const body = await r.json().catch(() => ({}));
  if (!r.ok)
    throw new Error(body.detail?.message || body.detail || "Request failed");
  return body;
}
const arr = (v: any): any[] => (Array.isArray(v) ? v : []);
const lines = (v: any) => arr(v).join("\n");
const list = (v: string) =>
  v
    .split("\n")
    .map((x) => x.trim())
    .filter(Boolean);

function formatReceivedAt(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function normalizeBrief(input: string): Brief {
  let raw: any;
  try {
    raw = JSON.parse(input);
  } catch {
    raw = { problem: input };
  }
  const source = raw.brief || raw.opportunity || raw.data || raw;
  const value = (...keys: string[]) =>
    keys
      .map((k) => source?.[k] ?? raw?.[k])
      .find((v) => v !== undefined && v !== null && v !== "");
  const now = new Date().toISOString();
  const id = String(
    value("id", "brief_id", "opportunity_id") || `B-CRM-${Date.now()}`,
  );
  return {
    id,
    account: String(
      value("account", "account_name", "company", "customer") ||
        "CRM opportunity",
    ),
    owner: String(
      value("owner", "owner_name", "assigned_to") || "US Solution Architect",
    ),
    region: String(value("region", "market") || "US"),
    segment: String(value("segment", "industry") || "enterprise"),
    regulator: String(value("regulator", "regulators") || "Not specified"),
    problem: String(
      value("problem", "business_problem", "brief", "description") ||
        "Customer requirements supplied by CRM event.",
    ),
    systems: arr(value("systems", "systems_customer_runs", "integrations")).map(
      String,
    ),
    expected_timeline: String(
      value("expected_timeline", "timeline") || "To be confirmed",
    ),
    success_criteria: arr(
      value("success_criteria", "poc_success_criteria", "success"),
    ).length
      ? arr(value("success_criteria", "poc_success_criteria", "success")).map(
          String,
        )
      : ["Confirm success criteria with customer"],
    received_at: String(
      value("received_at", "timestamp", "occurred_at") || now,
    ),
  };
}

function NewBriefDrawer() {
  const [open, setOpen] = useState(false);
  const [body, setBody] = useState(
    '{\n  "event_type": "opportunity_won",\n  "timestamp": "2026-09-05T14:30:00Z",\n  "owner": "US Solution Architect",\n  "brief": {\n    "account": "DemoCorp Financial",\n    "region": "US",\n    "segment": "retail_bank",\n    "regulator": "OCC",\n    "business_problem": "Customer service agents spend too much time retrieving account information.",\n    "systems_customer_runs": ["Salesforce", "Mainframe"],\n    "expected_timeline": "3 weeks",\n    "poc_success_criteria": "Surface consolidated customer data in under 5 seconds."\n  }\n}',
  );
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const click = (e: Event) => {
      if ((e.target as HTMLElement).closest(".test-brief"))
        setOpen(true);
    };
    window.addEventListener("click", click);
    return () => {
      window.removeEventListener("click", click);
    };
  }, []);
  if (!open) return null;
  const submit = async () => {
    setBusy(true);
    try {
      const brief = normalizeBrief(body);
      const response = await request("/api/briefs", {
        method: "POST",
        body: JSON.stringify(brief),
      });
      window.dispatchEvent(
        new CustomEvent("brief-created", { detail: response.brief }),
      );
      setOpen(false);
    } catch (e) {
      window.dispatchEvent(
        new CustomEvent("brief-error", { detail: String(e) }),
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="drawer-backdrop" onClick={() => setOpen(false)}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <div>
            <p className="eyebrow">CRM webhook simulator</p>
            <h2>Test New Brief</h2>
          </div>
          <button className="close" onClick={() => setOpen(false)}></button>
        </div>
        <p className="drawer-copy">
          Paste a HubSpot or Salesforce event as JSON, or paste plain-text brief
          content. It will be normalized, added to the queue, retrieved, and
          made ready for draft generation.
        </p>
        <label className="drawer-label">
          CRM event / brief
          <textarea
            className="crm-input"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            spellCheck={false}
          />
        </label>
        <div className="drawer-foot">
          <span className="muted">POST /api/briefs</span>
          <button className="primary" onClick={submit} disabled={busy}>
            {busy ? "Adding brief" : "Add to brief queue"}
          </button>
        </div>
      </aside>
    </div>
  );
}

function SkeletonLoader({ label = "Loading data" }: { label?: string }) {
  return (
    <div className="skeleton-loader" role="status" aria-label={label}>
      <span className="sr-only">{label}</span>
      <div className="skeleton-line skeleton-line-wide" />
      <div className="skeleton-line skeleton-line-medium" />
      <div className="skeleton-line skeleton-line-short" />
      <div className="skeleton-line skeleton-line-wide" />
    </div>
  );
}

function App() {
  const [items, setItems] = useState<Item[]>([]),
    [selected, setSelected] = useState<Item | null>(null),
    [provider, setProvider] = useState<"gemini" | "lm_studio">("gemini"),
    [matches, setMatches] = useState<Match[]>([]),
    [draft, setDraft] = useState<Draft | null>(null),
    [tab, setTab] = useState<"poc" | "handoff" | "reasoning">("poc"),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [loading, setLoading] = useState(false),
    [drawer, setDrawer] = useState(false);
  const load = async () => {
    try {
      const d = await request("/api/briefs");
      setItems(d.items);
      setSelected((c) =>
        c
          ? d.items.find((x: Item) => x.brief.id === c.brief.id) || d.items[0]
          : d.items[0],
      );
    } catch (e) {
      setError(String(e));
    }
  };
  useEffect(() => {
    load();
  }, []);
  useEffect(() => {
    if (selected?.draft) {
      setDraft(selected.draft.draft);
      setMatches(selected.draft.matches);
    } else {
      setDraft(null);
      setMatches([]);
    }
    setTab("poc");
  }, [selected]);
  const created = (item: Item) => {
    setItems((x) => [item, ...x]);
    setSelected(item);
    setDraft(null);
    setMatches([]);
    setNotice(
      "New CRM brief added to the queue. Select a provider and generate its draft.",
    );
  };
  useEffect(() => {
    const onCreated = (e: Event) =>
      created({
        brief: (e as CustomEvent).detail,
        health: {
          status: "GREEN",
          elapsed_business_days: 0,
          elapsed_business_hours: 0,
        },
      });
    const onError = (e: Event) => setError((e as CustomEvent).detail);
    window.addEventListener("brief-created", onCreated);
    window.addEventListener("brief-error", onError);
    return () => {
      window.removeEventListener("brief-created", onCreated);
      window.removeEventListener("brief-error", onError);
    };
  }, []);
  const generate = async () => {
    if (!selected) return;
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const d = await request(`/api/briefs/${selected.brief.id}/generate`, {
        method: "POST",
        body: JSON.stringify({ provider }),
      });
      setDraft(d.draft);
      setMatches(d.matches);
      setNotice(
        `Draft generated with ${provider === "gemini" ? "Gemini" : "LM Studio"}.`,
      );
      await load();
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };
  const decide = async (decision: "accepted" | "rejected") => {
    if (!selected || !draft) return;
    const reason =
      decision === "rejected"
        ? window.prompt("Why is this draft rejected?")
        : null;
    if (decision === "rejected" && !reason) return;
    try {
      const d = await request(`/api/briefs/${selected.brief.id}/decision`, {
        method: "POST",
        body: JSON.stringify({ decision, draft, rejection_reason: reason }),
      });
      setNotice(
        `${decision} recorded. Reuse rate: ${Math.round(d.reuse_rate * 100)}%.`,
      );
      await load();
    } catch (e) {
      setError(String(e));
    }
  };
  if (!selected)
    return (
      <main className="shell">
        <h1>RevenueOS</h1>
        <p>Loading brief queue</p>
      </main>
    );
  const b = selected.brief;
  const analysis = draft?.template_analysis || [];
  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Synthetic RevenueOS control surface</p>
          <h1>Brief POC Plan</h1>
          <p className="sub">Sales US PreSales handoff operations</p>
        </div>
        <div className="top-actions">
          <button
            className="secondary test-brief"
            onClick={() => setDrawer(true)}
          >
            {" "}
            Test New Brief
          </button>
          <div className="provider">
            <label>
              Agent provider
              <select
                value={provider}
                onChange={(e) =>
                  setProvider(e.target.value as "gemini" | "lm_studio")
                }
              >
                <option value="gemini">Gemini</option>
                <option value="lm_studio">LM Studio</option>
              </select>
            </label>
            <button className="primary" onClick={generate} disabled={loading}>
              {loading ? "Refreshing data…" : "Generate / refresh draft"}
            </button>
          </div>
        </div>
      </header>
      {error && (
        <div className="error">
          <strong>Provider/request error</strong>
          <span>{error}</span>
          <button onClick={generate}>Retry</button>
          <button onClick={() => setError("")}>Dismiss</button>
        </div>
      )}
      {notice && <div className="notice">{notice}</div>}
      <section className="workspace">
        <aside className="panel queue">
          <div className="panel-title">
            <h2>Brief queue</h2>
            <span>{items.length} open</span>
          </div>
          {items.map((i) => (
            <button
              className={`queue-item ${i.brief.id === b.id ? "active" : ""}`}
              key={i.brief.id}
              onClick={() => setSelected(i)}
            >
              <div>
                <strong>{i.brief.account}</strong>
                <small>
                  {i.brief.segment.replace("_", " ")} {i.brief.region}
                </small>
              </div>
              <span className={`badge ${i.health.status.toLowerCase()}`}>
                {i.health.status}
              </span>
            </button>
          ))}
        </aside>
        <div className="content">
          <section className="top-grid">
            <section className="panel brief">
              <div className="panel-title">
                <div>
                  <p className="eyebrow">
                    {b.id}
                  </p>
                  <h2>Won Opportunity Brief</h2>
                </div>
                <span
                  className={`badge ${selected.health.status.toLowerCase()}`}
                >
                  {selected.health.status}{" "}
                  {selected.health.elapsed_business_days}d
                </span>
              </div>
              <div className="facts">
                <div>
                  <small>Account</small>
                  <strong>{b.account}</strong>
                </div>
                <div>
                  <small>Owner</small>
                  <strong>{b.owner}</strong>
                </div>
                <div>
                  <small>Region / segment</small>
                  <strong>
                    {b.region} {b.segment.replace("_", " ")}
                  </strong>
                </div>
                <div>
                  <small>Regulator</small>
                  <strong>{b.regulator || "Not provided"}</strong>
                </div>
                <div>
                  <small>Expected timeline</small>
                  <strong>{b.expected_timeline}</strong>
                </div>
                <div>
                  <small>Received at</small>
                  <strong>{formatReceivedAt(b.received_at)}</strong>
                </div>
              </div>
              <p className="problem">{b.problem}</p>
              <div className="chips">
                {b.systems.map((x) => (
                  <span key={x}>{x}</span>
                ))}
              </div>
            </section>
            <section className="panel retrieval">
              <div className="panel-title">
                <h2>Top 3 retrieval analysis</h2>
                <span>{loading ? "Refreshing data…" : "Hybrid ranking why it matched"}</span>
              </div>
              {loading ? (
                <div className="matches">
                  <SkeletonLoader label="Refreshing retrieval analysis" />
                  <SkeletonLoader />
                  <SkeletonLoader />
                </div>
              ) : matches.length === 0 ? (
                <p className="muted">
                  Generate a draft to retrieve the top three templates.
                </p>
              ) : (
                <div className="matches">
                  {matches.map((m) => {
                    const a = analysis.find(
                      (x) => x.template_id === m.template.id,
                    );
                    return (
                      <article className="match" key={m.template.id}>
                        <div className="match-head">
                          <div>
                            <strong>
                              {m.template.id} {m.template.name}
                            </strong>
                            <small>
                              {m.template.region} {Math.round(m.score * 100)}%
                              engine score
                            </small>
                          </div>
                          <span className="score">
                            {Math.round(m.score * 100)}%
                          </span>
                        </div>
                        <span className="recommendation">
                          {a?.recommendation || "retrieved"}
                        </span>
                        <h3>Why it matched</h3>
                        <ul>
                          {arr(m.reasons).map((x) => (
                            <li key={x}>{x}</li>
                          ))}
                          {arr(a?.match_reasons)
                            .filter((x) => !m.reasons.includes(x))
                            .map((x) => (
                              <li key={x}>{x}</li>
                            ))}
                        </ul>
                        {arr(a?.mismatches).length > 0 && (
                          <>
                            <h3>Gaps</h3>
                            <p>{a?.mismatches.join(" ")}</p>
                          </>
                        )}
                        <h3>Changes required</h3>
                        <p>
                          {arr(a?.required_changes).join(" ") ||
                            "No changes stated by the agent."}
                        </p>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>
          </section>
          <section className="support-grid">
            <section className="panel">
              <div className="panel-title">
                <h2>Seam health</h2>
                <span>Computed 2 business-day SLA</span>
              </div>
              <div className="health-grid">
                <div className="metric">
                  <b>{selected.health.elapsed_business_days}d</b>
                  <small>Brief age</small>
                </div>
                <div className="metric">
                  <b>2d</b>
                  <small>SLA budget</small>
                </div>
                <div className="metric">
                  <b>{selected.health.status}</b>
                  <small>Current state</small>
                </div>
              </div>
              {selected.trigger && (
                <div className="banner">
                  SLA breached. Trigger created for{" "}
                  <b>{selected.trigger.owner}</b> with the current draft
                  attached.
                </div>
              )}
            </section>
            <section className="panel">
              <div className="panel-title">
                <h2>Event & trigger log</h2>
                <span>Computed from OS events</span>
              </div>
              <div className="event">
                <span className="dot" />
                <div>
                  <b>
                    {selected.trigger ? "seam.breached" : "opportunity.won"}
                  </b>
                  <small>
                    {selected.trigger
                      ? "Two-business-day SLA breach trigger created"
                      : "Won opportunity received and brief queued"}
                  </small>
                </div>
              </div>
              <div className="event">
                <span className="dot" />
                <div>
                  <b>templates.retrieved</b>
                  <small>Top 3 templates ranked with match evidence</small>
                </div>
              </div>
            </section>
          </section>
          <section className="panel draft">
            <div className="draft-head">
              <div>
                <p className="eyebrow">AI-assisted review</p>
                <h2>AI Draft Solution Architect Review</h2>
              </div>
              <div className="actions">
                <button className="secondary" onClick={() => setTab("poc")}>
                  Edit
                </button>
                <button
                  className="primary accept"
                  onClick={() => decide("accepted")}
                  disabled={!draft || loading}
                >
                  Accept
                </button>
                <button
                  className="danger"
                  onClick={() => decide("rejected")}
                  disabled={!draft || loading}
                >
                  Reject
                </button>
              </div>
            </div>
            <div className="tabs">
              <button
                className={tab === "poc" ? "active" : ""}
                onClick={() => setTab("poc")}
              >
                POC Plan
              </button>
              <button
                className={tab === "handoff" ? "active" : ""}
                onClick={() => setTab("handoff")}
              >
                Delivery Handoff
              </button>
              <button
                className={tab === "reasoning" ? "active" : ""}
                onClick={() => setTab("reasoning")}
              >
                Reuse Reasoning
              </button>
            </div>
            <div className="draft-body">
              {loading ? (
                <SkeletonLoader label="Generating AI draft" />
              ) : !draft ? (
                <p className="muted">
                  Choose a provider and generate an actionable POC plan.
                </p>
              ) : tab === "poc" ? (
                <>
                  <label>
                    Objective
                    <textarea
                      value={draft.poc_plan?.objective || ""}
                      onChange={(e) =>
                        setDraft({
                          ...draft,
                          poc_plan: {
                            ...draft.poc_plan,
                            objective: e.target.value,
                          },
                        })
                      }
                    />
                  </label>
                  <div className="two">
                    <label>
                      Scope in
                      <textarea
                        value={lines(draft.poc_plan?.scope_in)}
                        onChange={(e) =>
                          setDraft({
                            ...draft,
                            poc_plan: {
                              ...draft.poc_plan,
                              scope_in: list(e.target.value),
                            },
                          })
                        }
                      />
                    </label>
                    <label>
                      Scope out
                      <textarea
                        value={lines(draft.poc_plan?.scope_out)}
                        onChange={(e) =>
                          setDraft({
                            ...draft,
                            poc_plan: {
                              ...draft.poc_plan,
                              scope_out: list(e.target.value),
                            },
                          })
                        }
                      />
                    </label>
                  </div>
                  <div className="two">
                    <label>
                      Success criteria
                      <textarea
                        value={lines(draft.poc_plan?.success_criteria)}
                        onChange={(e) =>
                          setDraft({
                            ...draft,
                            poc_plan: {
                              ...draft.poc_plan,
                              success_criteria: list(e.target.value),
                            },
                          })
                        }
                      />
                    </label>
                    <label>
                      People required
                      <textarea
                        value={lines(draft.poc_plan?.people_required)}
                        onChange={(e) =>
                          setDraft({
                            ...draft,
                            poc_plan: {
                              ...draft.poc_plan,
                              people_required: list(e.target.value),
                            },
                          })
                        }
                      />
                    </label>
                  </div>
                  <h3>Weekly plan & risks</h3>
                  {arr(draft.poc_plan?.weekly_plan).map((w) => (
                    <p key={w.week}>
                      <b>Week {w.week}:</b> {arr(w.activities).join("  ")}
                    </p>
                  ))}
                  {arr(draft.poc_plan?.risks).map((r, i) => (
                    <p key={i}>
                      <b>Risk:</b> {r.risk || "Unspecified risk"}{" "}
                      <span className="muted">
                        {r.mitigation && `Mitigation: ${r.mitigation}`}
                      </span>
                    </p>
                  ))}
                </>
              ) : tab === "handoff" ? (
                <div>
                  <label>
                    Solution summary
                    <textarea
                      value={draft.delivery_handoff?.solution_summary || ""}
                      onChange={(e) =>
                        setDraft({
                          ...draft,
                          delivery_handoff: {
                            ...draft.delivery_handoff,
                            solution_summary: e.target.value,
                          },
                        })
                      }
                    />
                  </label>
                  <div className="two">
                    <div>
                      <h3>Account</h3>
                      <p>{draft.delivery_handoff?.account || b.account}</p>
                      <h3>Business problem</h3>
                      <p>
                        {draft.delivery_handoff?.business_problem || b.problem}
                      </p>
                      <h3>Approved scope</h3>
                      <ul>
                        {arr(draft.delivery_handoff?.approved_scope).map(
                          (x) => (
                            <li key={x}>{x}</li>
                          ),
                        )}
                      </ul>
                    </div>
                    <div>
                      <h3>Integrations</h3>
                      <ul>
                        {arr(draft.delivery_handoff?.integrations).map((x) => (
                          <li key={x}>{x}</li>
                        ))}
                      </ul>
                      <h3>Dependencies</h3>
                      <ul>
                        {arr(draft.delivery_handoff?.dependencies).map((x) => (
                          <li key={x}>{x}</li>
                        ))}
                      </ul>
                      <h3>Open questions</h3>
                      <ul>
                        {arr(
                          draft.delivery_handoff?.open_questions ||
                            draft.open_questions,
                        ).map((x) => (
                          <li key={x}>{x}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="reasoning-list">
                  {analysis.length === 0 ? (
                    <p className="muted">
                      Generate a draft to see agent reasoning.
                    </p>
                  ) : (
                    analysis.map((a) => (
                      <article key={a.template_id}>
                        <div className="match-head">
                          <strong>{a.template_id}</strong>
                          <span className="recommendation">
                            {a.recommendation}
                          </span>
                        </div>
                        <h3>Why this template is relevant</h3>
                        <ul>
                          {arr(a.match_reasons).map((x) => (
                            <li key={x}>{x}</li>
                          ))}
                        </ul>
                        <h3>Mismatches</h3>
                        <ul>
                          {arr(a.mismatches).length ? (
                            arr(a.mismatches).map((x) => <li key={x}>{x}</li>)
                          ) : (
                            <li>None identified</li>
                          )}
                        </ul>
                        <h3>Required changes</h3>
                        <ul>
                          {arr(a.required_changes).length ? (
                            arr(a.required_changes).map((x) => (
                              <li key={x}>{x}</li>
                            ))
                          ) : (
                            <li>None stated</li>
                          )}
                        </ul>
                      </article>
                    ))
                  )}
                </div>
              )}
            </div>
            <div className="statusbar">
              <b>{draft ? "Draft  human approval required" : "No draft"}</b>
              <span>AI can recommend. It cannot approve.</span>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
createRoot(document.getElementById("root")!).render(
  <>
    <React.StrictMode>
      <App />
      <NewBriefDrawer />
    </React.StrictMode>
  </>,
);
