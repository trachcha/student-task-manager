import { useCallback, useEffect, useRef, useState } from "react";

const SIDEBAR_MIN = 160;
const SIDEBAR_MAX = 480;
const SIDEBAR_DEFAULT = 240;
const SIDEBAR_STORAGE_KEY = "sidebar-width";

function clampWidth(value: number) {
  return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, value));
}

function readStoredWidth() {
  const stored = localStorage.getItem(SIDEBAR_STORAGE_KEY);
  if (!stored) {
    return SIDEBAR_DEFAULT;
  }
  const parsed = Number(stored);
  return Number.isFinite(parsed) ? clampWidth(parsed) : SIDEBAR_DEFAULT;
}

export function useSidebarWidth() {
  const [width, setWidth] = useState(readStoredWidth);
  const resizing = useRef(false);
  const widthRef = useRef(width);

  widthRef.current = width;

  const onResizeStart = useCallback((event: React.MouseEvent) => {
    event.preventDefault();
    resizing.current = true;
    document.body.classList.add("sidebar-resizing");
  }, []);

  useEffect(() => {
    function onMouseMove(event: MouseEvent) {
      if (!resizing.current) {
        return;
      }
      setWidth(clampWidth(event.clientX));
    }

    function onMouseUp() {
      if (!resizing.current) {
        return;
      }
      resizing.current = false;
      document.body.classList.remove("sidebar-resizing");
      localStorage.setItem(SIDEBAR_STORAGE_KEY, String(widthRef.current));
    }

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
    return () => {
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      document.body.classList.remove("sidebar-resizing");
    };
  }, []);

  return { width, onResizeStart };
}
