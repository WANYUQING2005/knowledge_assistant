import { useState, useCallback } from "react";
export const useHistory = (sessions = []) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSession, setSelectedSession] = useState(null);
  const filteredSessions = useState(() => {
    if (!searchQuery.trim()) {
      return sessions;
    }
    const query = searchQuery.toLowerCase();
    return sessions.filter((session) =>
      session.title?.toLowerCase().includes(query)
    );
  }, [sessions, searchQuery]);
  const selectSession = useCallback(
    (sessionId) => {
      const session = sessions.find(
        (s) => (s.session_id || s.id) === sessionId
      );
      setSelectedSession(session);
    },
    [sessions]
  );
  const clearSelection = useCallback(() => {
    setSelectedSession(null);
  }, []);
  const searchSessions = useCallback((query) => {
    setSearchQuery(query);
  }, []);
  const clearSearch = useCallback(() => {
    setSearchQuery("");
  }, []);
  const getSessionById = useCallback(
    (sessionId) => {
      return sessions.find((s) => (s.session_id || s.id) === sessionId);
    },
    [sessions]
  );
  const getRecentSessions = useCallback(
    (limit = 10) => {
      return sessions
        .slice()
        .sort(
          (a, b) =>
            new Date(b.update_at || b.create_at) -
            new Date(a.update_at || a.create_at)
        )
        .slice(0, limit);
    },
    [sessions]
  );
  return {
    searchQuery,
    selectedSession,
    filteredSessions,
    selectSession,
    clearSelection,
    searchSessions,
    clearSearch,
    getSessionById,
    getRecentSessions,
  };
};
