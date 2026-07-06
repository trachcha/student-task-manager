import { useCallback, useEffect, useRef, useState, type CSSProperties, type FormEvent } from "react";
import { ApiError, api } from "../api/client";
import type { Subject, Task, TaskFilters } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import TaskRowMenu from "../components/TaskRowMenu";
import { useSidebarWidth } from "../hooks/useSidebarWidth";
import {
  buildSidebarSubjects,
  DEFAULT_UNSORTED_LABEL,
  subjectIdForApi,
  taskSubjectIdForSelect,
  UNSORTED_SUBJECT_ID,
} from "../subjects/constants";
import SubjectPanel from "../subjects/SubjectPanel";
import SubtaskList from "../subtasks/SubtaskList";

type TaskView = "active" | "completed";

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed";
const COMPLETION_DELAY_MS = 600;

function readSidebarCollapsed() {
  return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
}

function mergeBucketOrder(bucketIds: number[], visibleIds: number[]): number[] {
  const visibleSet = new Set(visibleIds);
  const queue = [...visibleIds];
  return bucketIds.map((id) => (visibleSet.has(id) ? queue.shift()! : id));
}

export default function TaskListPage() {
  const { user, refreshUser } = useAuth();
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState<number | null>(null);
  const [taskView, setTaskView] = useState<TaskView>("active");
  const [newTitle, setNewTitle] = useState("");
  const [newSubjectId, setNewSubjectId] = useState<number | null>(null);
  const [expandedTaskId, setExpandedTaskId] = useState<number | null>(null);
  const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [confirmingDeleteTaskId, setConfirmingDeleteTaskId] = useState<number | null>(
    null,
  );
  const [openMenuTaskId, setOpenMenuTaskId] = useState<number | null>(null);
  const [draggingTaskId, setDraggingTaskId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editError, setEditError] = useState<string | null>(null);

  const subjectInputRef = useRef<HTMLInputElement>(null);
  const completionTimeoutsRef = useRef<Map<number, number>>(new Map());
  const { width: sidebarWidth, onResizeStart } = useSidebarWidth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(readSidebarCollapsed);
  const [localUnsortedPosition, setLocalUnsortedPosition] = useState<number | null>(null);
  const unsortedLabel = user?.unsorted_label ?? DEFAULT_UNSORTED_LABEL;
  const unsortedPosition = localUnsortedPosition ?? user?.unsorted_position ?? 0;
  const sidebarSubjects = buildSidebarSubjects(
    subjects,
    unsortedLabel,
    unsortedPosition,
  );
  const sortedSubjects = [...subjects].sort((a, b) =>
    a.name.localeCompare(b.name),
  );

  const canDrag =
    editingTaskId === null &&
    confirmingDeleteTaskId === null &&
    openMenuTaskId === null;

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

  const persistSubjectReorder = useCallback(
    async (reorderedSubjects: Subject[]) => {
      const subjectIds = reorderedSubjects.map((subject) => subject.id);
      const realSubjects = reorderedSubjects.filter(
        (subject) => subject.id !== UNSORTED_SUBJECT_ID,
      );
      const nextUnsortedPosition = reorderedSubjects.findIndex(
        (subject) => subject.id === UNSORTED_SUBJECT_ID,
      );
      setSubjects(realSubjects);
      setLocalUnsortedPosition(nextUnsortedPosition);
      setError(null);
      try {
        const updated = await api.reorderSubjects(subjectIds);
        setSubjects(updated);
        await refreshUser();
        setLocalUnsortedPosition(null);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not reorder subjects");
        setLocalUnsortedPosition(null);
        await loadSubjects();
        await refreshUser();
      }
    },
    [loadSubjects, refreshUser],
  );

  async function handleRenameUnsorted(name: string) {
    await api.updatePreferences({ unsorted_label: name });
    await refreshUser();
  }

  async function handleRenameSubject(id: number, name: string) {
    await api.updateSubject(id, name);
    await loadSubjects();
  }

  const loadTasks = useCallback(async () => {
    const filters: TaskFilters = {
      completed: taskView === "completed",
    };
    if (selectedSubjectId !== null && selectedSubjectId !== UNSORTED_SUBJECT_ID) {
      filters.subject_id = selectedSubjectId;
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
  }, [selectedSubjectId, taskView]);

  const persistReorder = useCallback(
    async (reorderedVisible: Task[]) => {
      const visibleIds = reorderedVisible.map((task) => task.id);
      setError(null);
      try {
        const bucket = await api.listTasks({ completed: taskView === "completed" });
        const bucketIds = bucket.map((task) => task.id);
        const fullOrder = mergeBucketOrder(bucketIds, visibleIds);
        await api.reorderTasks(taskView === "completed", fullOrder);
        await loadTasks();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not reorder tasks");
        await loadTasks();
      }
    },
    [loadTasks, taskView],
  );

  useEffect(() => {
    loadSubjects();
  }, [loadSubjects]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  useEffect(() => {
    setOpenMenuTaskId(null);
    setEditingTaskId(null);
    setConfirmingDeleteTaskId(null);
  }, [taskView, selectedSubjectId]);

  useEffect(() => {
    return () => {
      completionTimeoutsRef.current.forEach((timeoutId) => clearTimeout(timeoutId));
      completionTimeoutsRef.current.clear();
    };
  }, []);

  function clearCompletionTimeout(taskId: number) {
    const existing = completionTimeoutsRef.current.get(taskId);
    if (existing !== undefined) {
      clearTimeout(existing);
      completionTimeoutsRef.current.delete(taskId);
    }
  }

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!newTitle.trim()) {
      return;
    }
    setError(null);
    try {
      await api.createTask(newTitle.trim(), subjectIdForApi(newSubjectId));
      setNewTitle("");
      setNewSubjectId(null);
      if (taskView !== "active") {
        setTaskView("active");
      } else {
        await loadTasks();
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create task");
    }
  }

  async function handleToggle(task: Task) {
    const nextCompleted = !task.completed;
    setError(null);
    clearCompletionTimeout(task.id);

    if (taskView === "active" && nextCompleted) {
      setTasks((prev) =>
        prev.map((t) => (t.id === task.id ? { ...t, completed: true } : t)),
      );
      try {
        await api.updateTask(task.id, {
          title: task.title,
          completed: true,
          subject_id: task.subject_id,
        });
        const timeoutId = window.setTimeout(() => {
          completionTimeoutsRef.current.delete(task.id);
          setTasks((prev) => prev.filter((t) => t.id !== task.id));
        }, COMPLETION_DELAY_MS);
        completionTimeoutsRef.current.set(task.id, timeoutId);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not update task");
        await loadTasks();
      }
      return;
    }

    try {
      await api.updateTask(task.id, {
        title: task.title,
        completed: nextCompleted,
        subject_id: task.subject_id,
      });
      await loadTasks();
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
    setEditError(null);
    setOpenMenuTaskId(null);
  }

  function cancelEdit() {
    setEditingTaskId(null);
    setEditingTitle("");
    setEditError(null);
  }

  async function saveEdit(task: Task) {
    const title = editingTitle.trim();
    if (!title || title === task.title) {
      cancelEdit();
      return;
    }
    setEditError(null);
    try {
      await api.updateTask(task.id, {
        title,
        completed: task.completed,
        subject_id: task.subject_id,
      });
      cancelEdit();
      await loadTasks();
    } catch (err) {
      setEditError(err instanceof ApiError ? err.message : "Could not rename task");
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

  function handleSubtaskCountChange(taskId: number, count: number) {
    setTasks((prev) => {
      const task = prev.find((entry) => entry.id === taskId);
      if (task?.completed && count === 0) {
        setExpandedTaskId((current) => (current === taskId ? null : current));
      }
      return prev.map((entry) =>
        entry.id === taskId ? { ...entry, subtask_count: count } : entry,
      );
    });
  }

  function handleDragStart(event: React.DragEvent, taskId: number) {
    if (!canDrag) {
      event.preventDefault();
      return;
    }
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(taskId));
    setDraggingTaskId(taskId);
  }

  function handleDragOver(event: React.DragEvent) {
    if (!canDrag || draggingTaskId === null) {
      return;
    }
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }

  function handleDrop(event: React.DragEvent, targetId: number) {
    event.preventDefault();
    const sourceId = draggingTaskId;
    setDraggingTaskId(null);
    if (!sourceId || sourceId === targetId) {
      return;
    }

    const from = tasks.findIndex((task) => task.id === sourceId);
    const to = tasks.findIndex((task) => task.id === targetId);
    if (from < 0 || to < 0) {
      return;
    }

    const next = [...tasks];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    setTasks(next);
    void persistReorder(next);
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
        onReorder={persistSubjectReorder}
        onRenameUnsorted={handleRenameUnsorted}
        onRenameSubject={handleRenameSubject}
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
              value={newSubjectId ?? ""}
              onChange={(e) =>
                setNewSubjectId(e.target.value ? Number(e.target.value) : null)
              }
            >
              <option value="">Select subject</option>
              <option value={UNSORTED_SUBJECT_ID}>{unsortedLabel}</option>
              {sortedSubjects.map((subject) => (
                <option key={subject.id} value={subject.id}>
                  {subject.name}
                </option>
              ))}
            </select>
            <button type="submit">Add task</button>
          </form>

          <div className="task-view-toggle" role="tablist" aria-label="Task view">
            <button
              type="button"
              role="tab"
              aria-selected={taskView === "active"}
              className={taskView === "active" ? "active" : ""}
              onClick={() => setTaskView("active")}
            >
              Active
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={taskView === "completed"}
              className={taskView === "completed" ? "active" : ""}
              onClick={() => setTaskView("completed")}
            >
              Completed
            </button>
          </div>
        </div>

        {error && <p className="error">{error}</p>}

        <ul className="task-list">
          {tasks.length === 0 && (
            <li className="task-empty">
              {taskView === "active" ? "No active tasks." : "No completed tasks."}
            </li>
          )}
          {tasks.map((task) => {
            const showSubtasks = !task.completed || task.subtask_count > 0;

            return (
            <li
              key={task.id}
              className={`task-item${draggingTaskId === task.id ? " task-item--dragging" : ""}`}
              onDragOver={handleDragOver}
              onDrop={(event) => handleDrop(event, task.id)}
            >
              {editingTaskId === task.id && editError && (
                <p className="error task-item-error">{editError}</p>
              )}
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
                  <>
                    <button
                      type="button"
                      className="task-drag-handle"
                      draggable={canDrag}
                      onDragStart={(event) => handleDragStart(event, task.id)}
                      onDragEnd={() => setDraggingTaskId(null)}
                      aria-label="Reorder task"
                      disabled={!canDrag}
                    >
                      ≡
                    </button>
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
                  </>
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
                        <option value={UNSORTED_SUBJECT_ID}>{unsortedLabel}</option>
                        {sortedSubjects.map((subject) => (
                          <option key={subject.id} value={subject.id}>
                            {subject.name}
                          </option>
                        ))}
                      </select>
                      {showSubtasks && (
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
                      )}
                      <TaskRowMenu
                        isOpen={openMenuTaskId === task.id}
                        onToggle={() =>
                          setOpenMenuTaskId((current) =>
                            current === task.id ? null : task.id,
                          )
                        }
                        onClose={() => setOpenMenuTaskId(null)}
                        onRename={() => startEdit(task)}
                        onDelete={() => setConfirmingDeleteTaskId(task.id)}
                      />
                    </div>
                  ))}
              </div>
              {showSubtasks && expandedTaskId === task.id && (
                <SubtaskList
                  taskId={task.id}
                  parentCompleted={task.completed}
                  onCountChange={(count) => handleSubtaskCountChange(task.id, count)}
                />
              )}
            </li>
            );
          })}
        </ul>
      </section>
    </div>
  );
}
