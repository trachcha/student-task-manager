import { useCallback, useEffect, useRef, useState, type CSSProperties, type FormEvent } from "react";
import { ApiError, api } from "../api/client";
import type { Subject, Task, TaskFilters } from "../api/types";
import { useSidebarWidth } from "../hooks/useSidebarWidth";
import {
  subjectIdForApi,
  taskSubjectIdForSelect,
  UNSORTED_SUBJECT_ID,
  withUnsortedSubject,
} from "../subjects/constants";
import SubjectPanel from "../subjects/SubjectPanel";
import SubtaskList from "../subtasks/SubtaskList";

type CompletedFilter = "all" | "active" | "completed";

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed";

function readSidebarCollapsed() {
  return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
}

export default function TaskListPage() {
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [completedFilter, setCompletedFilter] = useState<CompletedFilter>("all");
  const [search, setSearch] = useState("");
  const [newTitle, setNewTitle] = useState("");
  const [newSubjectId, setNewSubjectId] = useState<number | null>(UNSORTED_SUBJECT_ID);
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null);
  const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [confirmingDeleteTaskId, setConfirmingDeleteTaskId] = useState<number | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);

  const subjectInputRef = useRef<HTMLInputElement>(null);
  const { width: sidebarWidth, onResizeStart } = useSidebarWidth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(readSidebarCollapsed);
  const sidebarSubjects = withUnsortedSubject(subjects);
  const sortedSubjects = [...subjects].sort((a, b) =>
    a.name.localeCompare(b.name),
  );

  function toggleSidebarCollapsed() {
    setSidebarCollapsed((collapsed) => {
      const next = !collapsed;
      localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(next));
      return next;
    });
  }

  const loadSubjects = useCallback(async () => {
    setSubjects(await api.listSubjects());
  }, []);

  const loadTasks = useCallback(async () => {
    const filters: TaskFilters = {};
    if (selectedSubjectId !== null && selectedSubjectId !== UNSORTED_SUBJECT_ID) {
      filters.subject_id = selectedSubjectId;
    }
    if (completedFilter !== "all") {
      filters.completed = completedFilter === "completed";
    }
    if (search.trim()) {
      filters.q = search.trim();
    }
    try {
      let loaded = await api.listTasks(filters);
      if (selectedSubjectId === UNSORTED_SUBJECT_ID) {
        loaded = loaded.filter((task) => task.subject_id === null);
      }
      setTasks(loaded);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load tasks");
    }
  }, [selectedSubjectId, completedFilter, search]);

  useEffect(() => {
    loadSubjects();
  }, [loadSubjects]);

  useEffect(() => {
    const handle = setTimeout(loadTasks, 200);
    return () => clearTimeout(handle);
  }, [loadTasks]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!newTitle.trim()) {
      return;
    }
    setError(null);
    try {
      await api.createTask(newTitle.trim(), subjectIdForApi(newSubjectId));
      setNewTitle("");
      await loadTasks();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create task");
    }
  }

  async function handleToggle(task: Task) {
    const nextCompleted = !task.completed;
    setTasks((prev) =>
      prev.map((t) =>
        t.id === task.id ? { ...t, completed: nextCompleted } : t,
      ),
    );
    try {
      await api.updateTask(task.id, {
        title: task.title,
        completed: nextCompleted,
        subject_id: task.subject_id,
      });
      if (completedFilter !== "all") {
        await loadTasks();
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update task");
      await loadTasks();
    }
  }

  async function handleSubjectChange(task: Task, subjectId: number | null) {
    setError(null);
    try {
      await api.updateTask(task.id, {
        title: task.title,
        completed: task.completed,
        subject_id: subjectIdForApi(subjectId),
      });
      await loadTasks();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update subject");
      await loadTasks();
    }
  }

  function startEdit(task: Task) {
    setEditingTaskId(task.id);
    setEditingTitle(task.title);
  }

  function cancelEdit() {
    setEditingTaskId(null);
    setEditingTitle("");
  }

  async function saveEdit(task: Task) {
    const title = editingTitle.trim();
    if (!title || title === task.title) {
      cancelEdit();
      return;
    }
    setError(null);
    try {
      await api.updateTask(task.id, {
        title,
        completed: task.completed,
        subject_id: task.subject_id,
      });
      cancelEdit();
      await loadTasks();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not rename task");
    }
  }

  async function handleDelete(task: Task) {
    setError(null);
    try {
      await api.deleteTask(task.id);
      setConfirmingDeleteTaskId(null);
      await loadTasks();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete task");
    }
  }

  return (
    <div
      className={`task-layout${sidebarCollapsed ? " sidebar-collapsed" : ""}`}
      style={
        sidebarCollapsed
          ? undefined
          : ({ "--sidebar-width": `${sidebarWidth}px` } as CSSProperties)
      }
    >
      <SubjectPanel
        subjects={sidebarSubjects}
        selectedSubjectId={selectedSubjectId}
        onSelect={setSelectedSubjectId}
        onChanged={(createdSubjectId) => {
          loadSubjects();
          loadTasks();
          if (createdSubjectId !== undefined) {
            setNewSubjectId(createdSubjectId);
          }
        }}
        inputRef={subjectInputRef}
        collapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebarCollapsed}
      />

      <div
        className="sidebar-resizer"
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize sidebar"
        onMouseDown={onResizeStart}
      />

      <section className="task-content">
        <div className="task-toolbar">
          <form className="task-create" onSubmit={handleCreate}>
            <input
              type="text"
              placeholder="Type your task"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
            />
            <select
              value={newSubjectId ?? UNSORTED_SUBJECT_ID}
              onChange={(e) => setNewSubjectId(Number(e.target.value))}
            >
              <option value="" disabled>
                Select subject
              </option>
              <option value={UNSORTED_SUBJECT_ID}>Unsorted</option>
              {sortedSubjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </select>
            <button type="submit">Add task</button>
          </form>

          <div className="task-filters">
            <input
              type="search"
              placeholder="Search tasks..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              value={completedFilter}
              onChange={(e) => setCompletedFilter(e.target.value as CompletedFilter)}
            >
              <option value="all">All</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>

        {error && <p className="error">{error}</p>}

        <ul className="task-list">
          {tasks.length === 0 && <li className="task-empty">No tasks found.</li>}
          {tasks.map((task) => (
            <li key={task.id} className="task-item">
              <div className="task-row">
                {editingTaskId === task.id ? (
                  <div className="task-main task-edit">
                    <input
                      type="text"
                      autoFocus
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") saveEdit(task);
                        if (e.key === "Escape") cancelEdit();
                      }}
                    />
                    <button type="button" onClick={() => saveEdit(task)}>
                      Save
                    </button>
                    <button type="button" onClick={cancelEdit}>
                      Cancel
                    </button>
                  </div>
                ) : (
                  <label className="task-main">
                    <input
                      type="checkbox"
                      checked={task.completed}
                      onChange={() => handleToggle(task)}
                    />
                    <span className={task.completed ? "done" : ""}>
                      {task.title}
                    </span>
                  </label>
                )}
                {editingTaskId !== task.id &&
                  (confirmingDeleteTaskId === task.id ? (
                    <div className="task-actions confirm-delete">
                      <span className="confirm-label">Delete this task?</span>
                      <button
                        type="button"
                        className="danger"
                        onClick={() => handleDelete(task)}
                      >
                        Delete
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfirmingDeleteTaskId(null)}
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="task-actions">
                      <select
                        value={taskSubjectIdForSelect(task.subject_id)}
                        onChange={(e) =>
                          handleSubjectChange(task, Number(e.target.value))
                        }
                      >
                        <option value="" disabled>
                          Select subject
                        </option>
                        <option value={UNSORTED_SUBJECT_ID}>Unsorted</option>
                        {sortedSubjects.map((subject) => (
                          <option key={subject.id} value={subject.id}>
                            {subject.name}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() =>
                          setExpandedTaskId(
                            expandedTaskId === task.id ? null : task.id,
                          )
                        }
                      >
                        {expandedTaskId === task.id ? "Hide" : "Subtasks"}
                      </button>
                      <button type="button" onClick={() => startEdit(task)}>
                        Rename
                      </button>
                      <button
                        type="button"
                        className="danger"
                        onClick={() => setConfirmingDeleteTaskId(task.id)}
                      >
                        Delete
                      </button>
                    </div>
                  ))}
              </div>
              {expandedTaskId === task.id && (
                <SubtaskList taskId={task.id} parentCompleted={task.completed} />
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
