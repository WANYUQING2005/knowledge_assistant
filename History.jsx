// components/History.jsx - 添加新建对话按钮
import { useState, useMemo, useEffect } from "react";
import styles from "./History.module.css";
import { formatChatTime } from "./utils/chatHelpers";
import KnowledgeSelector from "./KnowledgeSelector";

function History({
  sessions = [],
  currentSession,
  onSelectSession,
  onDeleteSession,
  onCreateNewChat,
  loading = false,
}) {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedSession, setExpandedSession] = useState(null);
  const [showNewChatKBPicker, setShowNewChatKBPicker] = useState(false); // 新增：控制新建对话的知识库选择器

  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) {
      return sessions;
    }
    const query = searchQuery.toLowerCase();
    return sessions.filter((session) =>
      session.title?.toLowerCase().includes(query)
    );
  }, [sessions, searchQuery]);

  useEffect(() => {
    if (expandedSession) {
      const sessionExists = sessions.some(
        (session) => (session.session_id || session.id) === expandedSession
      );
      if (!sessionExists) {
        setExpandedSession(null);
      }
    }
  }, [sessions, expandedSession]);

  const handleSessionClick = (session) => {
    setExpandedSession(null);
    onSelectSession?.(session.session_id || session.id);
  };

  const handleDeleteClick = async (e, session) => {
    e.stopPropagation();

    const sessionId = session.session_id || session.id;

    if (window.confirm(`确定要删除对话"${session.title}"吗？`)) {
      setExpandedSession(null);
      const success = await onDeleteSession?.(sessionId);
      if (!success) {
        console.error("删除会话失败");
      }
    }
  };

  const handleMenuToggle = (e, sessionId) => {
    e.stopPropagation();
    setExpandedSession(expandedSession === sessionId ? null : sessionId);
  };

  const handleNewChatKBConfirm = async (selectedKBs) => {
    if (selectedKBs && selectedKBs.length > 0) {
      setShowNewChatKBPicker(false);
      await onCreateNewChat?.(selectedKBs);
    }
  };

  const openNewChatKBPicker = () => {
    setShowNewChatKBPicker(true);
  };

  const closeNewChatKBPicker = () => {
    setShowNewChatKBPicker(false);
  };

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        !event.target.closest(`.${styles.menuBtn}`) &&
        !event.target.closest(`.${styles.sessionMenu}`)
      ) {
        setExpandedSession(null);
      }
    };

    if (expandedSession) {
      document.addEventListener("click", handleClickOutside);
      return () => document.removeEventListener("click", handleClickOutside);
    }
  }, [expandedSession]);

  const getSessionPreview = (session) => {
    if (session.last_message && session.last_message.trim()) {
      return session.last_message.length > 50
        ? session.last_message.substring(0, 50) + "..."
        : session.last_message;
    }
    if (session.chat_count && session.chat_count > 0) {
      return `${session.chat_count} 条消息`;
    }
    return "暂无消息";
  };
  return (
    <div className={styles.history}>
      <div className={styles.header}>
        <div className={styles.title}>对话历史</div>
        <button
          className={styles.newChatBtn}
          onClick={openNewChatKBPicker}
          title="新建对话"
        >
         新建对话
        </button>
      </div>

      <div className={styles.searchContainer}>
        <input
          type="text"
          placeholder="搜索对话..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className={styles.searchInput}
        />
        {searchQuery && (
          <button
            className={styles.clearSearch}
            onClick={() => setSearchQuery("")}
          >
            ×
          </button>
        )}
      </div>

      <div className={styles.sessionList}>
        {loading ? (
          <div className={styles.loading}>
            <div className={styles.loadingSpinner}></div>
            <span>加载中...</span>
          </div>
        ) : filteredSessions.length === 0 ? (
          <div className={styles.empty}>
            {searchQuery ? "没有找到匹配的对话" : "点击上方按钮开始新对话"}
          </div>
        ) : (
          filteredSessions.map((session) => {
            const sessionId = session.session_id || session.id;
            const isActive = currentSession?.session_id === sessionId;
            const isExpanded = expandedSession === sessionId;

            return (
              <div
                key={sessionId}
                className={`${styles.sessionItem} ${
                  isActive ? styles.active : ""
                }`}
                onClick={() => handleSessionClick(session)}
              >
                <div className={styles.sessionContent}>
                  <div className={styles.sessionHeader}>
                    <h4 className={styles.sessionTitle}>
                      {session.title || "新对话"}
                    </h4>
                    <div className={styles.sessionActions}>
                      <span className={styles.messageCount}>
                        {session.chat_count || 0}
                      </span>
                      <button
                        className={styles.menuBtn}
                        onClick={(e) => handleMenuToggle(e, sessionId)}
                      >
                        ⋯
                      </button>
                    </div>
                  </div>

                  <div className={styles.sessionMeta}>
                    <span className={styles.sessionPreview}>
                      {getSessionPreview(session)}
                    </span>
                    <span className={styles.sessionTime}>
                      {formatChatTime(
                        new Date(
                          session.update_at || session.create_at
                        ).getTime()
                      )}
                    </span>
                  </div>

                  {isExpanded && (
                    <div
                      className={styles.sessionMenu}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        className={styles.menuItem}
                        onClick={(e) => {
                          e.stopPropagation();
                          console.log("重命名对话");
                          setExpandedSession(null);
                        }}
                      >
                        重命名
                      </button>
                      <button
                        className={`${styles.menuItem} ${styles.deleteItem}`}
                        onClick={(e) => handleDeleteClick(e, session)}
                      >
                        删除
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className={styles.footer}>
        <div className={styles.stats}>
          <span>共 {sessions.length} 个对话</span>
          {searchQuery && <span>找到 {filteredSessions.length} 个</span>}
        </div>
      </div>

      {/* 新增：新建对话的知识库选择器弹窗 */}
      {showNewChatKBPicker && (
        <div className={styles.kbPickerOverlay} onClick={closeNewChatKBPicker}>
          <div onClick={(e) => e.stopPropagation()}>
            <KnowledgeSelector
              selectedKBs={[]}
              onKBChange={handleNewChatKBConfirm}
              onClose={closeNewChatKBPicker}
              className={styles.kbPickerModal}
            />
          </div>
        </div>
      )}
    </div>
  );
}

export default History;
