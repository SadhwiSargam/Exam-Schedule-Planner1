import React, { useState, useEffect } from "react";
import { api } from "./api.js";
import "./styles.css";

function Dashboard({ onNavigate }) {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newPlan, setNewPlan] = useState({ semester: 3, academic_year: "", start_date: "", end_date: "", title: "", description: "" });

  useEffect(() => { loadPlans(); }, []);

  async function loadPlans() {
    try {
      setLoading(true);
      const data = await api.getPlans();
      setPlans(data);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }

  async function handleCreate(e) {
    e.preventDefault();
    setError("");
    try {
      const plan = await api.createPlan(newPlan);
      setNewPlan({ semester: 3, academic_year: "", start_date: "", end_date: "", title: "", description: "" });
      loadPlans();
      onNavigate("configure", plan.id);
    } catch (e) { setError(e.message); }
  }

  if (loading) return <div className="panel">Loading...</div>;

  return (
    <div className="shell">
      <header>
        <div className="eyebrow">ACADEMIC TOOL</div>
        <h1>Exam Schedule Planner</h1>
        <p>Manage examination timetables for college semesters.</p>
      </header>

      <section className="panel">
        <div className="flex-between">
          <h2>Examination Plans</h2>
          <button className="secondary" onClick={() => onNavigate("create")}>+ New Plan</button>
        </div>
        {error && <p className="error">{error}</p>}
        {plans.length === 0 ? (
          <p className="muted">No plans yet. Create your first examination plan.</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Title</th><th>Semester</th><th>Academic Year</th><th>Period</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {plans.map(p => (
                  <tr key={p.id}>
                    <td>{p.title}</td>
                    <td>Sem {p.semester}</td>
                    <td>{p.academic_year}</td>
                    <td>{p.start_date} to {p.end_date}</td>
                    <td><span className="badge">Draft</span></td>
                    <td>
                      <button className="secondary small" onClick={() => onNavigate("configure", p.id)}>Open</button>
                      <button className="secondary small danger" onClick={() => api.deletePlan(p.id).then(loadPlans)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="panel" id="create-form">
        <h2>Create New Plan</h2>
        <form onSubmit={handleCreate} className="grid">
          <label>Semester<select value={newPlan.semester} onChange={e => setNewPlan({...newPlan, semester: Number(e.target.value)})} required>
            {[3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
          </select></label>
          <label>Academic Year<input value={newPlan.academic_year} onChange={e => setNewPlan({...newPlan, academic_year: e.target.value})} placeholder="2024-25" required /></label>
          <label>Start Date<input type="date" value={newPlan.start_date} onChange={e => setNewPlan({...newPlan, start_date: e.target.value})} required /></label>
          <label>End Date<input type="date" value={newPlan.end_date} onChange={e => setNewPlan({...newPlan, end_date: e.target.value})} required /></label>
          <label className="full">Title<input value={newPlan.title} onChange={e => setNewPlan({...newPlan, title: e.target.value})} placeholder="Odd Semester Examination" required /></label>
          <label className="full">Description<textarea value={newPlan.description} onChange={e => setNewPlan({...newPlan, description: e.target.value})} rows={2} /></label>
          <button className="full" type="submit">Create Plan</button>
        </form>
      </section>
    </div>
  );
}

function SemesterConfig({ planId, onBack, onNext }) {
  const [plan, setPlan] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getPlan(planId).then(setPlan).catch(e => setError(e.message));
  }, [planId]);

  async function handleSave() {
    if (!plan) return;
    setSaving(true); setError("");
    try {
      await api.updatePlan(planId, plan);
      onNext();
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  }

  if (!plan) return <div className="panel">Loading...</div>;

  return (
    <div className="shell">
      <header><div className="eyebrow">STEP 1</div><h1>Semester Configuration</h1></header>
      <section className="panel">
        {error && <p className="error">{error}</p>}
        <form className="grid" onSubmit={e => {e.preventDefault(); handleSave();}}>
          <label>Semester<select value={plan.semester} onChange={e => setPlan({...plan, semester: Number(e.target.value)})}><option value={3}>3</option><option value={4}>4</option><option value={5}>5</option><option value={6}>6</option><option value={7}>7</option><option value={8}>8</option></select></label>
          <label>Academic Year<input value={plan.academic_year} onChange={e => setPlan({...plan, academic_year: e.target.value})} /></label>
          <label>Start Date<input type="date" value={plan.start_date} onChange={e => setPlan({...plan, start_date: e.target.value})} /></label>
          <label>End Date<input type="date" value={plan.end_date} onChange={e => setPlan({...plan, end_date: e.target.value})} /></label>
          <label className="full">Title<input value={plan.title} onChange={e => setPlan({...plan, title: e.target.value})} /></label>
          <label className="full">Description<textarea value={plan.description || ""} onChange={e => setPlan({...plan, description: e.target.value})} rows={2} /></label>
          <div className="flex-between full">
            <button type="button" className="secondary" onClick={onBack}>Back</button>
            <button type="submit" disabled={saving}>{saving ? "Saving..." : "Save & Continue"}</button>
          </div>
        </form>
      </section>
    </div>
  );
}

function SubjectManager({ planId, onBack, onNext }) {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editId, setEditId] = useState(null);
  const [form, setForm] = useState({ code: "", name: "", category: "theory", internal_count: 3, internal_duration_minutes: 90, see_duration_minutes: 180, lab_internal_duration_minutes: 120, lab_external_duration_minutes: 180, mathematics_related: false, num_batches: 1 });

  useEffect(() => { load(); }, [planId]);
  async function load() { try { setLoading(true); setSubjects(await api.getSubjects(planId)); } catch (e) { setError(e.message); } finally { setLoading(false); } }

  async function handleSubmit(e) {
    e.preventDefault(); setError("");
    try {
      if (editId) { await api.updateSubject(planId, editId, form); setEditId(null); }
      else { await api.createSubject(planId, form); }
      setForm({ code: "", name: "", category: "theory", internal_count: 3, internal_duration_minutes: 90, see_duration_minutes: 180, lab_internal_duration_minutes: 120, lab_external_duration_minutes: 180, mathematics_related: false, num_batches: 1 });
      load();
    } catch (e) { setError(e.message); }
  }

  function startEdit(s) { setEditId(s.id); setForm(s); }
  function cancelEdit() { setEditId(null); setForm({ code: "", name: "", category: "theory", internal_count: 3, internal_duration_minutes: 90, see_duration_minutes: 180, lab_internal_duration_minutes: 120, lab_external_duration_minutes: 180, mathematics_related: false, num_batches: 1 }); }

  if (loading) return <div className="panel">Loading...</div>;

  return (
    <div className="shell">
      <header><div className="eyebrow">STEP 2</div><h1>Subject Management</h1><p>Add all subjects for this semester.</p></header>
      <section className="panel">
        {error && <p className="error">{error}</p>}
        <form onSubmit={handleSubmit} className="grid">
          <h3>{editId ? "Edit Subject" : "Add Subject"}</h3>
          <label>Code<input value={form.code} onChange={e => setForm({...form, code: e.target.value})} required /></label>
          <label>Name<input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></label>
          <label>Category<select value={form.category} onChange={e => setForm({...form, category: e.target.value})}><option value="theory">Theory</option><option value="practical">Practical</option><option value="both">Both</option></select></label>
          <label>IAT Count<select value={form.internal_count} onChange={e => setForm({...form, internal_count: Number(e.target.value)})}><option value={0}>0</option><option value={1}>1</option><option value={2}>2</option><option value={3}>3</option></select></label>
          <label>Internal Duration<input type="number" value={form.internal_duration_minutes} onChange={e => setForm({...form, internal_duration_minutes: Number(e.target.value)})} /></label>
          <label>SEE Duration<input type="number" value={form.see_duration_minutes} onChange={e => setForm({...form, see_duration_minutes: Number(e.target.value)})} /></label>
          <label>Lab Internal Duration<input type="number" value={form.lab_internal_duration_minutes} onChange={e => setForm({...form, lab_internal_duration_minutes: Number(e.target.value)})} /></label>
          <label>Lab External Duration<input type="number" value={form.lab_external_duration_minutes} onChange={e => setForm({...form, lab_external_duration_minutes: Number(e.target.value)})} /></label>
          <label>Batches<input type="number" value={form.num_batches} onChange={e => setForm({...form, num_batches: Number(e.target.value)})} min={1} /></label>
          <label className="check"><input type="checkbox" checked={form.mathematics_related} onChange={e => setForm({...form, mathematics_related: e.target.checked})} /> Mathematics-related (scheduled first)</label>
          <div className="flex-between full">
            {editId ? <button type="button" className="secondary" onClick={cancelEdit}>Cancel</button> : null}
            <button type="submit">{editId ? "Update" : "Add Subject"}</button>
          </div>
        </form>
      </section>
      <section className="panel">
        <h2>Subjects ({subjects.length})</h2>
        {subjects.length === 0 ? <p className="muted">No subjects added yet.</p> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Code</th><th>Name</th><th>Category</th><th>IATs</th><th>Int. Dur.</th><th>SEE Dur.</th><th>Lab Int.</th><th>Lab Ext.</th><th>Batches</th><th>Math</th><th>Actions</th></tr></thead>
              <tbody>
                {subjects.map(s => (
                  <tr key={s.id}>
                    <td>{s.code}</td><td>{s.name}</td><td>{s.category}</td><td>{s.internal_count}</td><td>{s.internal_duration_minutes}</td><td>{s.see_duration_minutes}</td><td>{s.lab_internal_duration_minutes}</td><td>{s.lab_external_duration_minutes}</td><td>{s.num_batches}</td><td>{s.mathematics_related ? "Yes" : "No"}</td>
                    <td>
                      <button className="secondary small" onClick={() => startEdit(s)}>Edit</button>
                      <button className="secondary small danger" onClick={() => api.deleteSubject(planId, s.id).then(load)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <div className="flex-between" style={{maxWidth: 1080, margin: "20px auto", padding: "0 20px"}}>
        <button className="secondary" onClick={onBack}>Back</button>
        <button onClick={onNext} disabled={subjects.length === 0}>Continue</button>
      </div>
    </div>
  );
}

function ScheduleConfig({ planId, onBack, onNext }) {
  const [config, setConfig] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { api.getConfig(planId).then(setConfig).catch(e => setError(e.message)); }, [planId]);

  async function handleSave() {
    if (!config) return;
    setSaving(true); setError("");
    try { await api.updateConfig(planId, config); onNext(); }
    catch (e) { setError(e.message); }
    finally { setSaving(false); }
  }

  if (!config) return <div className="panel">Loading...</div>;

  return (
    <div className="shell">
      <header><div className="eyebrow">STEP 3</div><h1>Scheduling Configuration</h1><p>Configure date windows, slots, and durations for all examination types.</p></header>
      <section className="panel">
        {error && <p className="error">{error}</p>}
        <form onSubmit={e => {e.preventDefault(); handleSave();}} className="grid">
          <h3>IAT Windows</h3>
          <label>IAT 1 Start<input type="date" value={config.iat1_start || ""} onChange={e => setConfig({...config, iat1_start: e.target.value || null})} /></label>
          <label>IAT 1 End<input type="date" value={config.iat1_end || ""} onChange={e => setConfig({...config, iat1_end: e.target.value || null})} /></label>
          <label>IAT 2 Start<input type="date" value={config.iat2_start || ""} onChange={e => setConfig({...config, iat2_start: e.target.value || null})} /></label>
          <label>IAT 2 End<input type="date" value={config.iat2_end || ""} onChange={e => setConfig({...config, iat2_end: e.target.value || null})} /></label>
          <label>IAT 3 Start<input type="date" value={config.iat3_start || ""} onChange={e => setConfig({...config, iat3_start: e.target.value || null})} /></label>
          <label>IAT 3 End<input type="date" value={config.iat3_end || ""} onChange={e => setConfig({...config, iat3_end: e.target.value || null})} /></label>

          <h3>IAT Time Slots</h3>
          <label>Morning Start<input type="time" value={config.iat_morning_start} onChange={e => setConfig({...config, iat_morning_start: e.target.value})} /></label>
          <label>Morning End<input type="time" value={config.iat_morning_end} onChange={e => setConfig({...config, iat_morning_end: e.target.value})} /></label>
          <label>Afternoon Start<input type="time" value={config.iat_afternoon_start} onChange={e => setConfig({...config, iat_afternoon_start: e.target.value})} /></label>
          <label>Afternoon End<input type="time" value={config.iat_afternoon_end} onChange={e => setConfig({...config, iat_afternoon_end: e.target.value})} /></label>

          <h3>Lab Internal Window</h3>
          <label>Start<input type="date" value={config.lab_internal_start || ""} onChange={e => setConfig({...config, lab_internal_start: e.target.value || null})} /></label>
          <label>End<input type="date" value={config.lab_internal_end || ""} onChange={e => setConfig({...config, lab_internal_end: e.target.value || null})} /></label>

          <h3>Lab External Window</h3>
          <label>Start<input type="date" value={config.lab_external_start || ""} onChange={e => setConfig({...config, lab_external_start: e.target.value || null})} /></label>
          <label>End<input type="date" value={config.lab_external_end || ""} onChange={e => setConfig({...config, lab_external_end: e.target.value || null})} /></label>
          <label>Max Batches/Day<input type="number" value={config.max_lab_batches_per_day} onChange={e => setConfig({...config, max_lab_batches_per_day: Number(e.target.value)})} min={1} /></label>

          <h3>SEE Window</h3>
          <label>Start<input type="date" value={config.see_start || ""} onChange={e => setConfig({...config, see_start: e.target.value || null})} /></label>
          <label>End<input type="date" value={config.see_end || ""} onChange={e => setConfig({...config, see_end: e.target.value || null})} /></label>
          <label>Gap Days<input type="number" value={config.see_gap_days} onChange={e => setConfig({...config, see_gap_days: Number(e.target.value)})} min={0} /></label>

          <h3>Weekend Policy</h3>
          <label className="check"><input type="checkbox" checked={config.weekend_exclude_saturday} onChange={e => setConfig({...config, weekend_exclude_saturday: e.target.checked})} /> Exclude Saturdays</label>
          <label className="check"><input type="checkbox" checked={config.weekend_exclude_sunday} onChange={e => setConfig({...config, weekend_exclude_sunday: e.target.checked})} /> Exclude Sundays</label>

          <div className="flex-between full">
            <button type="button" className="secondary" onClick={onBack}>Back</button>
            <button type="submit" disabled={saving}>{saving ? "Saving..." : "Save & Continue"}</button>
          </div>
        </form>
      </section>
    </div>
  );
}

function HolidayManager({ planId, onBack, onNext }) {
  const [holidays, setHolidays] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ date: "", name: "", description: "" });

  useEffect(() => { load(); }, [planId]);
  async function load() { try { setLoading(true); setHolidays(await api.getHolidays(planId)); } catch (e) { setError(e.message); } finally { setLoading(false); } }

  async function handleAdd(e) {
    e.preventDefault(); setError("");
    try { await api.createHoliday(planId, form); setForm({ date: "", name: "", description: "" }); load(); }
    catch (e) { setError(e.message); }
  }

  if (loading) return <div className="panel">Loading...</div>;

  return (
    <div className="shell">
      <header><div className="eyebrow">STEP 4</div><h1>Holiday Management</h1><p>Add holidays and non-working days. These will be excluded from all examination scheduling.</p></header>
      <section className="panel">
        {error && <p className="error">{error}</p>}
        <form onSubmit={handleAdd} className="grid">
          <h3>Add Holiday</h3>
          <label>Date<input type="date" value={form.date} onChange={e => setForm({...form, date: e.target.value})} required /></label>
          <label>Name<input value={form.name} onChange={e => setForm({...form, name: e.target.value})} required /></label>
          <label className="full">Description<textarea value={form.description} onChange={e => setForm({...form, description: e.target.value})} rows={2} /></label>
          <button type="submit">Add Holiday</button>
        </form>
      </section>
      <section className="panel">
        <h2>Holidays ({holidays.length})</h2>
        {holidays.length === 0 ? <p className="muted">No holidays configured.</p> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Name</th><th>Description</th><th>Actions</th></tr></thead>
              <tbody>
                {holidays.map(h => (
                  <tr key={h.id}><td>{h.date}</td><td>{h.name}</td><td>{h.description || "-"}</td>
                    <td><button className="secondary small danger" onClick={() => api.deleteHoliday(planId, h.id).then(load)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <div className="flex-between" style={{maxWidth: 1080, margin: "20px auto", padding: "0 20px"}}>
        <button className="secondary" onClick={onBack}>Back</button>
        <button onClick={onNext}>Continue</button>
      </div>
    </div>
  );
}

function TimetableGenerator({ planId, onBack }) {
  const [timetable, setTimetable] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [validating, setValidating] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    setGenerating(true); setError("");
    try { const data = await api.generateSchedule(planId, true); setTimetable(data); }
    catch (e) { setError(e.message); }
    finally { setGenerating(false); }
  }

  async function validate() {
    if (!timetable) return;
    setValidating(true); setError("");
    try { const data = await api.validateSchedule(planId); alert(data.valid ? "Schedule is valid" : "Conflicts: " + data.conflicts.join(", ")); }
    catch (e) { setError(e.message); }
    finally { setValidating(false); }
  }

  async function regenerate() {
    setGenerating(true); setError("");
    try { const data = await api.generateSchedule(planId, true); setTimetable(data); }
    catch (e) { setError(e.message); }
    finally { setGenerating(false); }
  }

  return (
    <div className="shell">
      <header><div className="eyebrow">STEP 5</div><h1>Timetable Generation</h1><p>Generate and validate the examination timetable.</p></header>
      <section className="panel">
        {error && <p className="error">{error}</p>}
        <div className="flex-between" style={{gap: "10px", flexWrap: "wrap"}}>
          <button onClick={generate} disabled={generating}>{generating ? "Generating..." : "Generate Timetable"}</button>
          <button onClick={regenerate} disabled={generating || !timetable}>{generating ? "Regenerating..." : "Regenerate"}</button>
          <button className="secondary" onClick={validate} disabled={validating || !timetable}>{validating ? "Validating..." : "Validate"}</button>
        </div>
        {timetable && timetable.validation.warnings.length > 0 && (
          <div className="warning" style={{marginTop: 12}}>
            <strong>Warnings:</strong>
            <ul>{timetable.validation.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
          </div>
        )}
        {timetable && timetable.validation.conflicts.length > 0 && (
          <div className="error" style={{marginTop: 12}}>
            <strong>Conflicts:</strong>
            <ul>{timetable.validation.conflicts.map((c, i) => <li key={i}>{c}</li>)}</ul>
          </div>
        )}
        {timetable && timetable.validation.unscheduled.length > 0 && (
          <div className="error" style={{marginTop: 12}}>
            <strong>Unscheduled:</strong>
            <ul>{timetable.validation.unscheduled.map((u, i) => <li key={i}>{u}</li>)}</ul>
          </div>
        )}
      </section>
      {timetable && (
        <section className="panel">
          <h2>Generated Timetable ({timetable.entries.length} entries)</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Day</th><th>Type</th><th>Code</th><th>Subject</th><th>Batch</th><th>Time</th><th>Status</th></tr></thead>
              <tbody>
                {timetable.entries.map((e, i) => {
                  const d = new Date(e.date + "T00:00:00");
                  const day = d.toLocaleDateString("en-US", { weekday: "short" });
                  return <tr key={i}><td>{e.date}</td><td>{day}</td><td>{e.assessment_type}</td><td>{e.subject_code}</td><td>{e.subject_name}</td><td>{e.batch_number > 1 ? e.batch_number : "-"}</td><td>{e.start_time} - {e.end_time}</td><td><span className={"badge " + e.status.toLowerCase()}>{e.status}</span></td></tr>;
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}
      <div className="flex-between" style={{maxWidth: 1080, margin: "20px auto", padding: "0 20px"}}>
        <button className="secondary" onClick={onBack}>Back</button>
        <button onClick={() => api.exportPDF(planId).then(blob => { const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url; a.download = `timetable-${planId}.pdf`; a.click(); })}>Export PDF</button>
      </div>
    </div>
  );
}

function TimetableViewer({ planId }) {
  const [timetable, setTimetable] = useState(null);
  const [filter, setFilter] = useState({ type: "", date: "", subject: "" });
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { api.getSchedule(planId).then(setTimetable).finally(() => setLoading(false)); }, [planId]);

  const filtered = timetable?.entries.filter(e => {
    if (filter.type && e.assessment_type !== filter.type) return false;
    if (filter.date && e.date !== filter.date) return false;
    if (filter.subject && e.subject_code !== filter.subject && !e.subject_name.toLowerCase().includes(filter.subject.toLowerCase())) return false;
    return true;
  }) || [];

  async function startEdit(entry) {
    setEditingId(entry.id);
    setEditForm({
      date: entry.date,
      start_time: entry.start_time,
      end_time: entry.end_time,
      batch_number: entry.batch_number,
    });
    setValidationResult(null);
    setError("");
  }

  function cancelEdit() {
    setEditingId(null);
    setEditForm({});
    setValidationResult(null);
  }

  async function validateEdit() {
    if (!editForm.date || !editForm.start_time || !editForm.end_time) {
      setError("All fields are required");
      return;
    }
    setValidating(true);
    setError("");
    try {
      const tempEntries = timetable.entries.map(e =>
        e.id === editingId ? { ...e, ...editForm } : e
      );
      const result = await api.validateScheduleEntries(planId, tempEntries);
      setValidationResult(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setValidating(false);
    }
  }

  async function saveEdit() {
    if (!editForm.date || !editForm.start_time || !editForm.end_time) {
      setError("All fields are required");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await api.updateScheduleEntry(planId, editingId, editForm);
      const updated = timetable.entries.map(e =>
        e.id === editingId ? { ...e, ...editForm, status: "manual" } : e
      );
      setTimetable({ ...timetable, entries: updated });
      cancelEdit();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  function getValidationStatus() {
    if (!validationResult) return null;
    if (!validationResult.valid) return "error";
    if (validationResult.conflicts.length > 0) return "warning";
    return "valid";
  }

  if (loading) return <div className="panel">Loading...</div>;

  return (
    <div className="shell">
      <header><div className="eyebrow">VIEW</div><h1>Timetable Viewer</h1></header>
      <section className="panel">
        <h2>Filters</h2>
        <div className="grid" style={{gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))"}}>
          <label>Exam Type<select value={filter.type} onChange={e => setFilter({...filter, type: e.target.value})}><option value="">All</option><option value="IAT 1">IAT 1</option><option value="IAT 2">IAT 2</option><option value="IAT 3">IAT 3</option><option value="Lab Internal">Lab Internal</option><option value="Lab External">Lab External</option><option value="SEE">SEE</option></select></label>
          <label>Date<input type="date" value={filter.date} onChange={e => setFilter({...filter, date: e.target.value})} /></label>
          <label>Subject<input value={filter.subject} onChange={e => setFilter({...filter, subject: e.target.value})} placeholder="Code or name" /></label>
        </div>
      </section>
      <section className="panel">
        <h2>Timetable ({filtered.length} entries)</h2>
        {filtered.length === 0 ? <p className="muted">No entries match the current filter.</p> : (
          <div className="table-wrap">
            <table>
              <thead><tr><th>Date</th><th>Day</th><th>Type</th><th>Code</th><th>Subject</th><th>Batch</th><th>Time</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>
                {filtered.map((e, i) => {
                  const d = new Date(e.date + "T00:00:00");
                  const day = d.toLocaleDateString("en-US", { weekday: "short" });
                  const isEditing = editingId === e.id;
                  return (
                    <tr key={i}>
                      {isEditing ? (
                        <>
                          <td><input type="date" value={editForm.date} onChange={ev => setEditForm({...editForm, date: ev.target.value})} /></td>
                          <td>{day}</td>
                          <td>{e.assessment_type}</td>
                          <td>{e.subject_code}</td>
                          <td>{e.subject_name}</td>
                          <td><input type="number" value={editForm.batch_number} onChange={ev => setEditForm({...editForm, batch_number: Number(ev.target.value)})} min={1} /></td>
                          <td>
                            <input type="time" value={editForm.start_time} onChange={ev => setEditForm({...editForm, start_time: ev.target.value})} />
                            -
                            <input type="time" value={editForm.end_time} onChange={ev => setEditForm({...editForm, end_time: ev.target.value})} />
                          </td>
                          <td><span className="badge manual">Editing</span></td>
                          <td>
                            <button className="secondary small" onClick={validateEdit} disabled={validating}>{validating ? "Checking..." : "Validate"}</button>
                            <button onClick={saveEdit} disabled={saving}>{saving ? "Saving..." : "Save"}</button>
                            <button className="secondary small danger" onClick={cancelEdit}>Cancel</button>
                          </td>
                        </>
                      ) : (
                        <>
                          <td>{e.date}</td>
                          <td>{day}</td>
                          <td>{e.assessment_type}</td>
                          <td>{e.subject_code}</td>
                          <td>{e.subject_name}</td>
                          <td>{e.batch_number > 1 ? e.batch_number : "-"}</td>
                          <td>{e.start_time} - {e.end_time}</td>
                          <td><span className={"badge " + e.status.toLowerCase()}>{e.status}</span></td>
                          <td>
                            <button className="secondary small" onClick={() => startEdit(e)}>Edit</button>
                            <button className="secondary small danger" onClick={() => api.deleteScheduleEntry(planId, e.id).then(() => {
                              setTimetable({ ...timetable, entries: timetable.entries.filter(x => x.id !== e.id) });
                            })}>Delete</button>
                          </td>
                        </>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        {validationResult && (
          <div className={getValidationStatus() === "error" ? "error" : getValidationStatus() === "warning" ? "warning" : "success"} style={{marginTop: 12}}>
            <strong>Validation Result:</strong>
            {getValidationStatus() === "valid" && <span> No conflicts found. Schedule is valid.</span>}
            {getValidationStatus() === "warning" && (
              <ul style={{margin: "8px 0 0 20px"}}>
                {validationResult.conflicts.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            )}
            {getValidationStatus() === "error" && (
              <ul style={{margin: "8px 0 0 20px"}}>
                {validationResult.conflicts.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            )}
          </div>
        )}
        {error && <p className="error" style={{marginTop: 12}}>{error}</p>}
      </section>
    </div>
  );
}

export default function App() {
  const [view, setView] = useState("dashboard");
  const [planId, setPlanId] = useState(null);

  const views = {
    dashboard: () => <Dashboard onNavigate={(v, id) => { if (id) setPlanId(id); setView(v); }} />,
    create: () => <Dashboard onNavigate={(v, id) => { if (id) setPlanId(id); setView(v); }} />,
    configure: () => planId ? <SemesterConfig planId={planId} onBack={() => setView("dashboard")} onNext={() => setView("subjects")} /> : <Dashboard onNavigate={(v, id) => { if (id) setPlanId(id); setView(v); }} />,
    subjects: () => planId ? <SubjectManager planId={planId} onBack={() => setView("configure")} onNext={() => setView("schedule-config")} /> : <Dashboard onNavigate={(v, id) => { if (id) setPlanId(id); setView(v); }} />,
    "schedule-config": () => planId ? <ScheduleConfig planId={planId} onBack={() => setView("subjects")} onNext={() => setView("holidays")} /> : <Dashboard onNavigate={(v, id) => { if (id) setPlanId(id); setView(v); }} />,
    holidays: () => planId ? <HolidayManager planId={planId} onBack={() => setView("schedule-config")} onNext={() => setView("generate")} /> : <Dashboard onNavigate={(v, id) => { if (id) setPlanId(id); setView(v); }} />,
    generate: () => planId ? <TimetableGenerator planId={planId} onBack={() => setView("holidays")} /> : <Dashboard onNavigate={(v, id) => { if (id) setPlanId(id); setView(v); }} />,
    view: () => planId ? <TimetableViewer planId={planId} /> : <Dashboard onNavigate={(v, id) => { if (id) setPlanId(id); setView(v); }} />,
  };

  return (
    <div style={{minHeight: "100vh"}}>
      {planId && view !== "dashboard" && view !== "create" && (
        <nav className="top-nav">
          <div className="nav-inner">
            <span className="nav-title">Plan: {planId}</span>
            <div className="nav-links">
              <button className={view==="configure"?"active":""} onClick={() => setView("configure")}>Semester</button>
              <button className={view==="subjects"?"active":""} onClick={() => setView("subjects")}>Subjects</button>
              <button className={view==="schedule-config"?"active":""} onClick={() => setView("schedule-config")}>Schedule Config</button>
              <button className={view==="holidays"?"active":""} onClick={() => setView("holidays")}>Holidays</button>
              <button className={view==="generate"?"active":""} onClick={() => setView("generate")}>Generate</button>
              <button className={view==="view"?"active":""} onClick={() => setView("view")}>View</button>
              <button className="secondary" onClick={() => { setPlanId(null); setView("dashboard"); }}>Back to Dashboard</button>
            </div>
          </div>
        </nav>
      )}
      <main>{views[view]?.() || views.dashboard()}</main>
    </div>
  );
}