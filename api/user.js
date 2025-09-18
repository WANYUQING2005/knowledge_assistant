import http from "./http";
import NewKnowledge from './../NewKnowledge';
export const register = (payload) => http.post("accounts/register/", payload);
export const login = (payload) => http.post("accounts/login/", payload);
export const createKnowledgeLibrary = (payload) =>
  http.post("knowledge/create/", payload);
export const listKnowledge = (user_id, params = {}) =>
  http.get("/knowledge/list/", { params: { userid: user_id, ...params } });
const extToType = (name) => {
  const ext = (name.split(".").pop() || "").toLowerCase();
  if (["md", "markdown"].includes(ext)) return "markdown";
  if (["txt"].includes(ext)) return "text";
  if (["pdf"].includes(ext)) return "pdf";
  if (["doc", "docx"].includes(ext)) return "docx";
  if (["ppt", "pptx"].includes(ext)) return "pptx";
  if (["xlsx", "xls", "csv"].includes(ext)) return "sheet";
  return "file";
};
export  const deleteKnowledgeBase = async (NewKnowledge_base_id)=>{
    http.delete(`knowledge/delete/?knowledge_base_id=${NewKnowledge_base_id}`)
}
export const deleteDocument = async (documentid)=>{
    http.delete(`knowledge/documents/delete/?document_id=${documentid}`)
}
export async function listDocuments(kb_id) {
  const { data } = await http.get("knowledge/documents/list/", {
    params: { kb_id },
  });
  return Array.isArray(data) ? data : data?.results || [];
}
export async function uploadDocument({ kb_id, file, title, onProgress }) {
  const fd = new FormData();
  fd.append("knowledge_base_id", kb_id);
  fd.append("kb_id", kb_id);
  fd.append("title", title || file.name);
  fd.append("file_type", extToType(file.name));
  fd.append("file", file);
  const res = await http.post("knowledge/documents/upload/", fd, {
    timeout: 120000,
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress({
          loaded: e.loaded,
          total: e.total,
          percent: Math.round((e.loaded / e.total) * 100),
          name: file.name,
        });
      }
    },
  });
  return res.data ?? res;
}
export async function uploadDocuments({ kb_id, files, onProgress,llm_choice }) {
  const arr = Array.from(files);
  const results = [];
  for (let i = 0; i < arr.length; i++) {
    const file = arr[i];
    const r = await uploadDocument({
      kb_id,
      file,
      title: file.name,
      llm_choice,
      onProgress: (p) => onProgress && onProgress({ index: i, ...p }),
    });
    results.push(r);
  }
  return results;
}
export async function documentDetail(documentid) {
  const { data } = await http.get("knowledge/documents/detail/", {
    params: { documentid },
  });
  return data;
}
