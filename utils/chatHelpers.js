export const generateMessageId = () => {
  return Date.now().toString() + Math.random().toString(36).substr(2, 9);
};
export const formatChatTime = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date - 28600000;
  if (diff < 60000) {
    return "刚刚";
  }
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)}分钟前`;
  }
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`;
  }
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }
  return date.toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};
export const createUserMessage = (content) => {
  return {
    id: generateMessageId(),
    sender: "user",
    content,
    create_at: new Date().toISOString(),
  };
};
export const validateMessage = (content) => {
  if (!content || typeof content !== "string") {
    return { valid: false, error: "消息内容不能为空" };
  }
  if (content.trim().length === 0) {
    return { valid: false, error: "消息内容不能为空" };
  }
  if (content.length > 4000) {
    return { valid: false, error: "消息内容过长，请控制在4000字符以内" };
  }
  return { valid: true };
};
export const extractKnowledgeRefs = (sources) => {
  if (!Array.isArray(sources)) return [];
  console.log('Raw sources from API:', sources);
  const uniqueSources = [];
  const seenTitles = new Set();
  sources.forEach((source, index) => {
    console.log(`Processing source ${index}:`, source);
    const title = source.title || source.name || `文档${index + 1}`;
    let documentId = null;
    if (source.source && source.source.includes('documents/')) {
      const match = source.source.match(/documents\/\d+\/([a-f0-9\-]+)/);
      if (match) {
        documentId = match[1]; // 提取UUID部分
        console.log(`Extracted document ID from source path: ${documentId}`);
      }
    }
    if (!documentId) {
      documentId = source.id || source.document_id || source.doc_id || source.kb_id;
    }
    console.log(`Final document ID for "${title}":`, documentId);
    if (!seenTitles.has(title)) {
      seenTitles.add(title);
      uniqueSources.push({
        id: documentId,
        name: title,
        source: source,
        kb_id: source.kb_id,
        snippet: source.snippet,
        score: source.score
      });
    }
  });

  console.log('Final extracted KB refs:', uniqueSources);
  return uniqueSources;
};



