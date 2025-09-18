import http from "./http";

export const createChatSession = (payload) =>
  http.post("chat/sessions/create/", payload);
export const getChatSessions = (user_id) =>
  http.get("chat/sessions/list/", { params: { user_id } });
export const getChatSessionDetail = (session_id) =>
  http.get("chat/session/detail/", { params: { session_id } });
export const sendChatMessage = (payload) =>
  http.post("chat/messages/send/", payload);
export const deleteChatSession = (session_id) =>
  http.post("chat/sessions/delete/", {
    session_id,
    user_id: localStorage.getItem("user_id") || "5",
  });
