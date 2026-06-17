import ThemeToggle from "../ThemeToggle";
import { useTheme } from "../../hooks/useTheme";
import { useAuth } from "../../context/useAuth";
import { useNavigate } from "react-router-dom";

interface PageLayoutProps {
  children: React.ReactNode;
}

export default function PageLayout({ children }: PageLayoutProps) {
  const { isDark, toggle } = useTheme();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 transition-colors">
      <div className="fixed top-6 right-6 z-50 flex items-center gap-3">
        {user && (
          <button
            onClick={() => navigate("/profile")}
            className="h-10 w-10 rounded-full
              bg-gray-900 dark:bg-white text-white dark:text-gray-900
              border border-gray-200 dark:border-gray-700
              flex items-center justify-center text-sm font-semibold
              hover:opacity-90 transition-colors cursor-pointer"
            aria-label="Open profile"
            title="Profile"
          >
            {user.first_name?.charAt(0) || "U"}
          </button>
        )}
        {user && (
          <button
            onClick={handleLogout}
            className="rounded-full px-4 py-2
              bg-white dark:bg-gray-900
              text-gray-700 dark:text-gray-200
              border border-gray-200 dark:border-gray-700
              hover:bg-gray-100 dark:hover:bg-gray-800
              transition-colors text-sm font-medium cursor-pointer"
            aria-label="Log out"
          >
            Log out
          </button>
        )}
        {!user && (
          <button
            onClick={() => navigate("/login")}
            className="rounded-full px-4 py-2
              bg-gray-900 dark:bg-white text-white dark:text-gray-900
              hover:bg-gray-800 dark:hover:bg-gray-100
              transition-colors text-sm font-medium cursor-pointer"
            aria-label="Log in"
          >
            Log in
          </button>
        )}
        <ThemeToggle isDark={isDark} onToggle={toggle} />
      </div>
      <div className="max-w-5xl mx-auto px-4 py-10">{children}</div>
    </div>
  );
}
