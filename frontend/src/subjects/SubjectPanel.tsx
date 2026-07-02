import { useState, type FormEvent, type RefObject } from "react";
import { ApiError, api } from "../api/client";
import type { Subject } from "../api/types";
import { UNSORTED_SUBJECT_ID } from "./constants";

interface SubjectPanelProps {
  subjects: Subject[];
  selectedSubjectId: number | null;
  onSelect: (subjectId: number | null) => void;
  onChanged: (createdSubjectId?: number) => void;
  inputRef?: RefObject<HTMLInputElement>;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export default function SubjectPanel({
  subjects,
  selectedSubjectId,
  onSelect,
  onChanged,
  inputRef,
  collapsed,
  onToggleCollapse,
}: SubjectPanelProps) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<number | null>(null);

  async function handleAdd(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }
    setError(null);
    try {
      const created = await api.createSubject(name.trim());
      setName("");
      onChanged(created.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add subject");
    }
  }

  async function handleDelete(subject: Subject) {
    await api.deleteSubject(subject.id);
    setConfirmingDeleteId(null);
    if (selectedSubjectId === subject.id) {
      onSelect(null);
    }
    onChanged();
  }

  return (
    <aside className={`subject-panel${collapsed ? " subject-panel--collapsed" : ""}`}>
      <div className="subject-panel-header">
        <h2>Subjects</h2>
        <button
          type="button"
          className="subject-panel-toggle"
          onClick={onToggleCollapse}
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Expand subjects panel" : "Collapse subjects panel"}
          title={collapsed ? "Expand subjects" : "Collapse subjects"}
        >
          {collapsed ? "›" : "‹"}
        </button>
      </div>

      {!collapsed && (
        <div className="subject-panel-body">
          <ul className="subject-list">
            <li>
              <button
                type="button"
                className={selectedSubjectId === null ? "active" : ""}
                onClick={() => onSelect(null)}
              >
                All tasks
              </button>
            </li>
            {subjects.map((subject) => (
              <li key={subject.id}>
                {confirmingDeleteId === subject.id ? (
                  <div className="confirm-delete">
                    <span className="confirm-label">Delete "{subject.name}"?</span>
                    <button
                      type="button"
                      className="icon-button danger"
                      title="Confirm delete"
                      onClick={() => handleDelete(subject)}
                    >
                      ✓
                    </button>
                    <button
                      type="button"
                      className="icon-button"
                      title="Cancel"
                      onClick={() => setConfirmingDeleteId(null)}
                    >
                      x
                    </button>
                  </div>
                ) : (
                  <>
                    <button
                      type="button"
                      className={selectedSubjectId === subject.id ? "active" : ""}
                      onClick={() => onSelect(subject.id)}
                    >
                      {subject.name}
                    </button>
                    {subject.id !== UNSORTED_SUBJECT_ID && (
                      <button
                        type="button"
                        className="icon-button"
                        title="Delete subject"
                        onClick={() => setConfirmingDeleteId(subject.id)}
                      >
                        x
                      </button>
                    )}
                  </>
                )}
              </li>
            ))}
          </ul>

          <form className="subject-form" onSubmit={handleAdd}>
            <input
              ref={inputRef}
              type="text"
              placeholder="New subject"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <button type="submit">Add</button>
          </form>
          {error && <p className="error">{error}</p>}
        </div>
      )}
    </aside>
  );
}
