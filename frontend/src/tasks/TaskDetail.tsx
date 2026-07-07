import { useEffect, useState } from "react";
import type { Task, TaskPriority, TaskUpdateInput } from "../api/types";

interface TaskDetailProps {
  task: Task;
  onSave: (data: TaskUpdateInput) => Promise<void>;
}

const PRIORITY_OPTIONS: { value: TaskPriority; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
];

export default function TaskDetail({ task, onSave }: TaskDetailProps) {
  const [description, setDescription] = useState(task.description ?? "");
  const [priority, setPriority] = useState<TaskPriority>(task.priority);
  const [dueDate, setDueDate] = useState(task.due_date ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDescription(task.description ?? "");
    setPriority(task.priority);
    setDueDate(task.due_date ?? "");
    setError(null);
  }, [task]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await onSave({
        title: task.title,
        description: description.trim() || null,
        priority,
        due_date: dueDate || null,
        completed: task.completed,
        subject_id: task.subject_id,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save task details");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="task-detail">
      {error && <p className="error">{error}</p>}
      <label className="task-detail-field">
        <span className="task-detail-label">Description</span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Add a description for this task"
          rows={3}
        />
      </label>
      <div className="task-detail-row">
        <label className="task-detail-field">
          <span className="task-detail-label">Priority</span>
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as TaskPriority)}
          >
            {PRIORITY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="task-detail-field">
          <span className="task-detail-label">Due date</span>
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
          />
        </label>
      </div>
      <div className="task-detail-actions">
        <button type="button" onClick={() => void handleSave()} disabled={saving}>
          {saving ? "Saving..." : "Save details"}
        </button>
      </div>
    </div>
  );
}
