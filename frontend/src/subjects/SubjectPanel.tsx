import { useState, type FormEvent, type RefObject } from "react";
import { ApiError, api } from "../api/client";
import type { Subject } from "../api/types";
import { UNSORTED_SUBJECT_ID } from "./constants";

interface SubjectPanelProps {
  subjects: Subject[];
  selectedSubjectId: number | null;
  onSelect: (subjectId: number | null) => void;
  onChanged: (createdSubjectId?: number) => void;
  onReorder: (reorderedSubjects: Subject[]) => Promise<void>;
  onRenameUnsorted: (name: string) => Promise<void>;
  onRenameSubject: (id: number, name: string) => Promise<void>;
  inputRef?: RefObject<HTMLInputElement>;
  collapsed: boolean;
  onToggleCollapse: () => void;
}

export default function SubjectPanel({
  subjects,
  selectedSubjectId,
  onSelect,
  onChanged,
  onReorder,
  onRenameUnsorted,
  onRenameSubject,
  inputRef,
  collapsed,
  onToggleCollapse,
}: SubjectPanelProps) {
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState("");
  const [editError, setEditError] = useState<string | null>(null);
  const [draggingSubjectId, setDraggingSubjectId] = useState<number | null>(null);

  const canDrag =
    editingId === null && confirmingDeleteId === null;

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

  function startEdit(subject: Subject) {
    setEditingId(subject.id);
    setEditingName(subject.name);
    setEditError(null);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditingName("");
    setEditError(null);
  }

  async function saveEdit(subject: Subject) {
    const trimmed = editingName.trim();
    if (!trimmed || trimmed === subject.name) {
      cancelEdit();
      return;
    }
    setEditError(null);
    try {
      if (subject.id === UNSORTED_SUBJECT_ID) {
        await onRenameUnsorted(trimmed);
      } else {
        await onRenameSubject(subject.id, trimmed);
      }
      cancelEdit();
      onChanged();
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : "Could not rename subject");
    }
  }

  function handleDragStart(event: React.DragEvent, subjectId: number) {
    if (!canDrag) {
      event.preventDefault();
      return;
    }
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(subjectId));
    setDraggingSubjectId(subjectId);
  }

  function handleDragOver(event: React.DragEvent) {
    if (!canDrag || draggingSubjectId === null) {
      return;
    }
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }

  function handleDrop(event: React.DragEvent, targetId: number) {
    event.preventDefault();
    const sourceId = draggingSubjectId;
    setDraggingSubjectId(null);
    if (!sourceId || sourceId === targetId) {
      return;
    }

    const from = subjects.findIndex((subject) => subject.id === sourceId);
    const to = subjects.findIndex((subject) => subject.id === targetId);
    if (from < 0 || to < 0) {
      return;
    }

    const next = [...subjects];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    void onReorder(next);
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
                className={`subject-name${selectedSubjectId === null ? " active" : ""}`}
                onClick={() => onSelect(null)}
              >
                All tasks
              </button>
            </li>
            {subjects.map((subject) => (
              <li
                key={subject.id}
                className={`subject-item${draggingSubjectId === subject.id ? " subject-item--dragging" : ""}`}
                onDragOver={handleDragOver}
                onDrop={(event) => handleDrop(event, subject.id)}
              >
                {editingId === subject.id ? (
                  <div className="subject-edit">
                    <input
                      type="text"
                      autoFocus
                      value={editingName}
                      onChange={(e) => setEditingName(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") void saveEdit(subject);
                        if (e.key === "Escape") cancelEdit();
                      }}
                    />
                    <button type="button" onClick={() => void saveEdit(subject)}>
                      Save
                    </button>
                    <button type="button" onClick={cancelEdit}>
                      Cancel
                    </button>
                    {editError && <p className="error">{editError}</p>}
                  </div>
                ) : confirmingDeleteId === subject.id ? (
                  <div className="confirm-delete">
                    <span className="confirm-label">Delete "{subject.name}"?</span>
                    <button
                      type="button"
                      className="icon-button danger"
                      title="Confirm delete"
                      onClick={() => void handleDelete(subject)}
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
                      className="subject-drag-handle"
                      draggable={canDrag}
                      onDragStart={(event) => handleDragStart(event, subject.id)}
                      onDragEnd={() => setDraggingSubjectId(null)}
                      aria-label="Reorder subject"
                      disabled={!canDrag}
                    >
                      ≡
                    </button>
                    <button
                      type="button"
                      className={`subject-name${selectedSubjectId === subject.id ? " active" : ""}`}
                      onClick={() => onSelect(subject.id)}
                      onDoubleClick={() => startEdit(subject)}
                      title="Double-click to rename"
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
