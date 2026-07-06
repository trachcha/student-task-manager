import { Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import ThemeToggle from "./ThemeToggle";

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="app">
      <header className="app-header">
        <h1>Student Task Manager</h1>
        <div className="app-header-user">
          <span>{user?.username}</span>
          <ThemeToggle />
          <button type="button" onClick={logout}>
            Log out
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
