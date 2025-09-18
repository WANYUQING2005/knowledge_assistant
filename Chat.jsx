import { useState, useEffect } from "react";
import styles from "./Chat.module.css";
import Conversation from "./Conversation";
import Header from "./Header";
import History from "./History";
import KnowledgeSelector from "./KnowledgeSelector";
import { useChat } from "./hooks/useChat";
import { listKnowledge } from "./api/user";
function Chat() {
  const {
    sessions,
    currentSession,
    messages,
    loading,
    sending,
    error,
    currentKBIds,
    loadSessions, 
    createSessionWithKB,
    selectSession,
    sendMessage,
    deleteSession,
    updateSessionKBs,
    clearError,
  } = useChat();

  const [selectedKBs, setSelectedKBs] = useState([]);
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [isKBPickerOpen, setIsKBPickerOpen] = useState(false);
  useEffect(() => {
    const loadKnowledgeBases = async () => {
      try {
        const user_id = localStorage.getItem("user_id") || "5";
        const response = await listKnowledge(user_id);
        const kbs = response.data || [];
        const formattedKBs = kbs.map((kb) => ({
          id: kb.id,
          name: kb.name,
          description: kb.description,
          updated: kb.updated_at,
          size: kb.document_count ? `${kb.document_count}个文档` : "",
        }));
        setKnowledgeBases(formattedKBs);
        console.log("Loaded knowledge bases:", formattedKBs);
      } catch (err) {
        console.error("Failed to load knowledge bases:", err);
      }
    };
    loadKnowledgeBases();
  }, []);
  useEffect(() => {
    if (currentKBIds.length > 0 && knowledgeBases.length > 0) {
      const sessionKBs = knowledgeBases.filter((kb) =>
        currentKBIds.includes(kb.id)
      );
      if (sessionKBs.length > 0) {
        setSelectedKBs(sessionKBs);
        console.log("Auto-selected KBs for session:", sessionKBs);
      }
    } else if (currentKBIds.length === 0) {
      setSelectedKBs([]);
    }
  }, [currentKBIds, knowledgeBases]);
  const handleSendMessage = async (content) => {
    return await sendMessage(content);
  };
  const handleCopy = (text) => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
      })
      .catch((err) => {
        console.error("复制失败:", err);
      });
  };
  const handleSelectSession = (sessionId) => {
    console.log("Selecting session:", sessionId);
    selectSession(sessionId);
  };
  const handleDeleteSession = async (sessionId) => {
    const success = await deleteSession(sessionId);
    if (success) {
      console.log("Session deleted successfully");
    } else {
      console.error("Failed to delete session");
    }
    return success;
  };
  const handleCreateNewChat = async (selectedKBs) => {
    console.log("Creating new chat from History with KBs:", selectedKBs);
    try {
      const newSession = await createSessionWithKB(
        selectedKBs,
        `与${selectedKBs[0].name}的对话`
      );
      if (newSession) {
        console.log("New session created successfully:", newSession);
        await loadSessions();
        setSelectedKBs(selectedKBs);
      }
    } catch (error) {
      console.error("Error creating new chat:", error);
    }
  };
  const handleKBConfirm = async (selected) => {
    console.log("KB selection confirmed:", selected);
    if (!selected || selected.length === 0) {
      console.warn("No knowledge base selected");
      return;
    }
    setSelectedKBs(selected);
    if (currentSession) {
      updateSessionKBs(selected);
      console.log("Updated KB for existing session:", selected);
    } else {
      try {
        const newSession = await createSessionWithKB(
          selected,
          `与${selected[0].name}的对话`
        );
        if (newSession) {
          console.log("Session created successfully:", newSession);
          await loadSessions();
        }
      } catch (error) {
        console.error("Error creating session:", error);
      }
    }
  };
  const openKBPicker = () => {
    setIsKBPickerOpen(true);
  };
  const closeKBPicker = () => {
    setIsKBPickerOpen(false);
  };
  const getKBButtonText = () => {
    if (selectedKBs.length > 0) {
      if (selectedKBs.length === 1) {
        return `已选择: ${selectedKBs[0].name}`;
      } else {
        return `已选择: ${selectedKBs[0].name} 等${selectedKBs.length}个`;
      }
    }
    return currentSession ? "切换知识库" : "选择知识库开始对话";
  };
  return (
    <div className={styles.mainPage}>
      <Header />
      {error && (
        <div className={styles.errorBanner}>
          <span>{error}</span>
          <button onClick={clearError}>×</button>
        </div>
      )}
      <div className={styles.primary}>
        <History
          sessions={sessions}
          currentSession={currentSession}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          onCreateNewChat={handleCreateNewChat} 
          loading={loading}
        />
        <Conversation
          messages={messages}
          onSend={handleSendMessage}
          onCopy={handleCopy}
          sending={sending}
          selectedKBs={selectedKBs}
          placeholder={
            currentSession
              ? `基于${
                  selectedKBs.length > 0
                    ? selectedKBs.map((kb) => kb.name).join("、")
                    : "知识库"
                }回答问题，回车发送（Shift+Enter 换行）`
              : `请先选择知识库开始对话`
          }
        />

        <div className={styles.kbToggle}>
          <button
            className={`${styles.kbButton} ${
              selectedKBs.length > 0 ? styles.kbButtonSelected : ""
            }`}
            onClick={openKBPicker}
          >
            {getKBButtonText()}
          </button>
        </div>
        {isKBPickerOpen && (
          <div className={styles.kbPickerOverlay} onClick={closeKBPicker}>
            <div onClick={(e) => e.stopPropagation()}>
              <KnowledgeSelector
                selectedKBs={selectedKBs}
                onKBChange={handleKBConfirm}
                onClose={closeKBPicker}
                className={styles.kbPickerModal}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Chat;
