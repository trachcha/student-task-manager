import { useEffect, useRef } from "react";

interface TaskRowMenuProps {
  isOpen: boolean;
  onToggle: () => void;
  onClose: () => void;
  onRename: () => void;
  onDelete: () => void;
}

export default function TaskRowMenu({
  isOpen,
  onToggle,
  onClose,
  onRename,
  onDelete,
}: TaskRowMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    function handlePointerDown(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        onClose();
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);

  return (
    <div className="task-menu" ref={menuRef}>
      <button
        type="button"
        className="task-menu-trigger"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        onClick={onToggle}
      >
        ⋯
      </button>
      {isOpen && (
        <div className="task-menu-dropdown" role="menu">
          <button
            type="button"
            role="menuitem"
            onClick={() => {
              onClose();
              onRename();
            }}
          >
            Rename
          </button>
          <button
            type="button"
            role="menuitem"
            className="danger"
            onClick={() => {
              onClose();
              onDelete();
            }}
          >
            Delete
          </button>
        </div>
      )}
    </div>
  );
}
