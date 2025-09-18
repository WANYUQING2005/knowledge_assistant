import { useState, useEffect, useCallback, useRef } from "react";
import {
  createChatSession,
  getChatSessions,
  getChatSessionDetail,
  sendChatMessage,
  deleteChatSession,
} from "../api/chat";
import {
  generateMessageId,
  validateMessage,
  extractKnowledgeRefs,
  createUserMessage,
} from "../utils/chatHelpers";

export const useChat = () => {
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState(null);
  const [currentKBIds, setCurrentKBIds] = useState([]); // 当前对话使用的知识库ID列表
  const currentSessionRef = useRef(null);
  const loadSessionsRef = useRef(false);
  const loadSessions = useCallback(async () => {
    if (loadSessionsRef.current) return;
    try {
      loadSessionsRef.current = true;
      setLoading(true);
      setError(null);
      const user_id = localStorage.getItem("user_id") || "5";
      const response = await getChatSessions(user_id);
      console.log("Sessions response:", response);
      if (response.data?.status === "success") {
        setSessions(response.data.data || []);
      } else {
        console.warn("Unexpected response format:", response);
        setSessions([]);
      }
    } catch (err) {
      console.error("Load sessions error:", err);
      setError("获取会话列表失败: " + (err.message || "未知错误"));
      setSessions([]);
    } finally {
      setLoading(false);
      loadSessionsRef.current = false;
    }
  }, []);
  const createSessionWithKB = useCallback(
    async (selectedKBs, title = "新对话") => {
      console.log("createSessionWithKB called with:", selectedKBs, title);
      if (!selectedKBs || selectedKBs.length === 0) {
        const errorMsg = "必须选择至少一个知识库才能创建对话";
        setError(errorMsg);
        console.error(errorMsg, selectedKBs);
        return null;
      }
      try {
        setLoading(true);
        setError(null);
        const user_id = localStorage.getItem("user_id") || "5";
        const primaryKB = Array.isArray(selectedKBs)
          ? selectedKBs[0]
          : selectedKBs;
        const payload = {
          user_id,
          ai_type: 1,
          kb_id: primaryKB.id,
          title,
        };
        console.log("Creating session with payload:", payload);
        const response = await createChatSession(payload);
        console.log("Create session response:", response);
        if (response.data?.status === "success") {
          const newSession = response.data.data;
          const kbIds = Array.isArray(selectedKBs)
            ? selectedKBs.map((kb) => kb.id)
            : [primaryKB.id];
          setCurrentKBIds(kbIds);
          setSessions((prev) => [newSession, ...prev]);
          setCurrentSession({ ...newSession, kb_ids: kbIds }); 
          setMessages([]);
          currentSessionRef.current = newSession.session_id;
          console.log("Session created successfully with KB IDs:", kbIds);
          return newSession;
        } else {
          throw new Error(
            "创建会话失败: " + (response.data?.message || "未知错误")
          );
        }
      } catch (err) {
        console.error("Create session error:", err);
        setError("创建会话失败: " + (err.message || "未知错误"));
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );
  const selectSession = useCallback(async (sessionId) => {
    if (currentSessionRef.current === sessionId) return;
    try {
      setLoading(true);
      setError(null);
      console.log("Selecting session:", sessionId);
      const response = await getChatSessionDetail(sessionId);
      console.log("Session detail response:", response);
      if (response.data?.status === "success") {
        const sessionData = response.data.data;
        const sessionInfo = {
          session_id: sessionId,
          ...sessionData,
        };
        setCurrentSession(sessionInfo);
        const kbIds = sessionInfo.kb_ids || [sessionInfo.kb_id].filter(Boolean);
        setCurrentKBIds(kbIds);
        console.log("Set current KB IDs for session:", kbIds);
        const formattedMessages = (sessionData.messages || []).map(
          (msg, index) => {
            const baseMessage = {
              id: msg.id || generateMessageId(),
              role: msg.sender === "user" ? "user" : "assistant",
              content: msg.content,
              time: new Date(msg.create_at || Date.now()).getTime(),
            };
            if (msg.sender === "ai") {
              let sources = null;

              if (msg.metadata && msg.metadata.sources) {
                sources = msg.metadata.sources;
              } else if (msg.sources) {
                sources = msg.sources;
              } else if (msg.metadata && typeof msg.metadata === "string") {
                try {
                  const parsedMetadata = JSON.parse(msg.metadata);
                  if (parsedMetadata.sources) {
                    sources = parsedMetadata.sources;
                  }
                } catch (e) {
                  console.warn(
                    "Failed to parse metadata as JSON:",
                    msg.metadata
                  );
                }
              }
              if (sources && Array.isArray(sources)) {
                console.log(
                  "Processing sources for historical message:",
                  msg.id,
                  sources
                );
                baseMessage.kbRefs = extractKnowledgeRefs(sources);
                baseMessage.rawSources = sources;
              }
            }
            return baseMessage;
          }
        );
        console.log("Formatted messages with sources:", formattedMessages);
        setMessages(formattedMessages);
        currentSessionRef.current = sessionId;
      } else {
        throw new Error(
          "获取会话详情失败: " + (response.data?.message || "未知错误")
        );
      }
    } catch (err) {
      console.error("Select session error:", err);
      setError("获取会话详情失败: " + (err.message || "未知错误"));
    } finally {
      setLoading(false);
    }
  }, []);
  const updateSessionKBs = useCallback(
    (selectedKBs) => {
      const kbIds = selectedKBs.map((kb) => kb.id);
      setCurrentKBIds(kbIds);
      if (currentSession) {
        setCurrentSession((prev) => ({ ...prev, kb_ids: kbIds }));
      }

      console.log("Updated session KB IDs:", kbIds);
    },
    [currentSession]
  );
  const sendMessage = useCallback(
    async (content) => {
      const validation = validateMessage(content);
      if (!validation.valid) {
        setError(validation.error);
        return false;
      }
      if (!currentSession?.session_id) {
        setError("请先选择知识库创建对话");
        return false;
      }
      if (!currentKBIds || currentKBIds.length === 0) {
        setError("请先选择知识库");
        return false;
      }
      try {
        setSending(true);
        setError(null);
        const userMessage = {
          id: generateMessageId(),
          role: "user",
          content,
          time: Date.now(),
        };
        setMessages((prev) => [...prev, userMessage]);
        const user_id = localStorage.getItem("user_id") || "5";
        const payload = {
          session_id: currentSession.session_id,
          user_id,
          sender: "user",
          content,
          kb_id: currentKBIds[0],
          kb_ids: currentKBIds, 
        };
        console.log("Sending message with payload (including kb_id):", payload);
        const response = await sendChatMessage(payload);
        console.log("Send message response:", response);
        if (response.data?.status === "success") {
          const aiResponse = response.data;
          console.log("AI response sources:", aiResponse.sources);
          const aiMessage = {
            id: generateMessageId(),
            role: "assistant",
            content: aiResponse.answer,
            time: Date.now(),
            kbRefs: aiResponse.sources
              ? extractKnowledgeRefs(aiResponse.sources)
              : undefined,
            rawSources: aiResponse.sources,
            metadata: {
              sources: aiResponse.sources,
              kb_ids: currentKBIds, 
            },
          };
          console.log("AI message with processed kbRefs:", aiMessage);
          setMessages((prev) => [...prev, aiMessage]);
          setSessions((prev) =>
            prev.map((session) =>
              session.session_id === currentSession.session_id
                ? {
                    ...session,
                    chat_count: (session.chat_count || 0) + 2,
                    update_at: new Date().toISOString(),
                    last_message: content,
                  }
                : session
            )
          );
          return true;
        } else {
          throw new Error(
            "发送消息失败: " + (response.data?.message || "未知错误")
          );
        }
      } catch (err) {
        console.error("Send message error:", err);
        setError("发送消息失败: " + (err.message || "未知错误"));
        setMessages((prev) => prev.slice(0, -1));
        return false;
      } finally {
        setSending(false);
      }
    },
    [currentSession, currentKBIds]
  );
  const deleteSession = useCallback(
    async (sessionId) => {
      try {
        setError(null);
        console.log("Deleting session:", sessionId);
        const response = await deleteChatSession(sessionId);
        console.log("Delete session response:", response);
        if (response.data?.status === "success" || response.status === 200) {
          setSessions((prev) => {
            const updated = prev.filter(
              (session) => session.session_id !== sessionId
            );
            console.log("Sessions after deletion:", updated);
            return updated;
          });
          if (currentSession?.session_id === sessionId) {
            setCurrentSession(null);
            setMessages([]);
            setCurrentKBIds([]);
            currentSessionRef.current = null;
          }
          return true; 
        } else {
          throw new Error(
            "删除会话失败: " + (response.data?.message || "未知错误")
          );
        }
      } catch (err) {
        console.error("Delete session error:", err);
        setError("删除会话失败: " + (err.message || "未知错误"));
        return false;
      }
    },
    [currentSession]
  );
  useEffect(() => {
    loadSessions();
  }, [loadSessions]);
  return {
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
    clearError: () => setError(null),
  };
};
