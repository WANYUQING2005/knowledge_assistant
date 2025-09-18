import { useEffect, useMemo, useRef, useState } from "react";
import styles from "./Conversation.module.css";
import DocumentSnippetPreview from "./DocumentSnippetPreview"; 

function MsgBubble({ m, isUser, onCopy, onDocumentClick }) {
  const handleRefClick = (ref) => {
    console.log("Ref clicked, full ref object:", ref);
    if (ref.source && ref.source.snippet) {
      const snippetData = {
        title: ref.source.title || ref.name,
        snippet: ref.source.snippet,
        score: ref.source.score,
        kb_id: ref.source.kb_id,
        source: ref.source.source,
      };
      onDocumentClick?.(snippetData);
    } else {
      console.error("No snippet found in ref:", ref);
      alert("无法获取文档片段信息");
    }
  };

return (
  <div className={`${styles.row} ${isUser ? styles.user : styles.assistant}`}>
    <div className={styles.bubble}>
      <div className={styles.header}>
        <span className={styles.role}>{isUser ? "我" : "助手"}</span>
        <div className={styles.meta}>
          {!isUser && m.kbRefs?.length > 0 && (
            <div className={styles.refs}>
              {Array.from(new Set(m.kbRefs.map((kb) => kb.name))).map(
                (name, index) => {
                  const ref = m.kbRefs.find((kb) => kb.name === name);
                  return (
                    <button
                      key={`${name}-${index}`}
                      className={styles.refChip}
                      onClick={() => handleRefClick(ref)}
                      title={`点击查看文档片段: ${name}`}
                    >
                      {name}
                    </button>
                  );
                }
              )}
            </div>
          )}
          <button className={styles.copy} onClick={() => onCopy?.(m.content)}>
            复制
          </button>
        </div>
      </div>
      <div className={styles.content}>{m.content}</div>
      {m.attach && <img className={styles.image} src={m.attach} alt="" />}
    </div>
  </div>
);
}
export default function Conversation({
  messages = [],
  onSend,
  onCopy,
  onAttach,
  sending = false,
  placeholder = "输入你的问题，回车发送（Shift+Enter 换行）",
  selectedKBs = [],
}) {
  const [value, setValue] = useState("");
  const [previewSnippet, setPreviewSnippet] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const endRef = useRef(null);
  const fileRef = useRef(null);

   const ordered = useMemo(() => {
     const sortedMessages = messages.slice().sort((a, b) => {
       if (a.time && b.time && a.time !== b.time) {
         return a.time - b.time;
       }
       const aIndex = messages.indexOf(a);
       const bIndex = messages.indexOf(b);
       return aIndex - bIndex;
     });
     const orderedMessages = [];
     let userMessages = sortedMessages.filter((m) => m.role === "user");
     let assistantMessages = sortedMessages.filter(
       (m) => m.role === "assistant"
     );
     const maxLength = Math.max(userMessages.length, assistantMessages.length);
     for (let i = 0; i < maxLength; i++) {
       if (userMessages[i]) {
         orderedMessages.push(userMessages[i]);
       }
       if (assistantMessages[i]) {
         orderedMessages.push(assistantMessages[i]);
       }
     }

     return orderedMessages;
   }, [messages]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [ordered.length]);

  const doSend = () => {
    const text = value.trim();
    if (!text || sending) return;
    onSend?.(text);
    setValue("");
  };

  const onKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      doSend();
    }
  };
  const onPick = (e) => {
    if (e.target.files?.length && onAttach) onAttach(e.target.files);
    e.target.value = "";
  };
  const handleDocumentClick = (snippetData) => {
    console.log("Document snippet clicked:", snippetData);
    setPreviewSnippet(snippetData);
    setShowPreview(true);
  };
  const closePreview = () => {
    setShowPreview(false);
    setPreviewSnippet(null);
  };
  return (
    <div className={styles.wrap}>
      <div className={styles.list}>
        {ordered.map((m) => (
          <MsgBubble
            key={m.id}
            m={m}
            isUser={m.role === "user"}
            onCopy={onCopy}
            onDocumentClick={handleDocumentClick}
          />
        ))}
        <div ref={endRef} />
      </div>
      <div className={styles.composer}>
        <div className={styles.kbRow}>
          <span className={styles.kbLabel}>已选知识库</span>
          <div className={styles.kbChips}>
            {selectedKBs.length === 0 && (
              <span className={styles.kbChipMuted}>未选择</span>
            )}
            {selectedKBs.map((kb) => (
              <span key={kb.id} className={styles.kbChip}>
                {kb.name}
              </span>
            ))}
          </div>
        </div>
        <div className={styles.inputWrap}>
          {onAttach && (
            <>
              <button
                className={styles.attach}
                type="button"
                onClick={() => fileRef.current?.click()}
                aria-label="上传文件"
                title="上传文件"
              >
                <svg
                  viewBox="0 0 24 24"
                  width="18"
                  height="18"
                  aria-hidden="true"
                >
                  <path
                    d="M21 15V7a5 5 0 0 0-10 0v10a3 3 0 0 1-6 0V9"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
              <input
                ref={fileRef}
                className={styles.file}
                type="file"
                multiple
                onChange={onPick}
              />
            </>
          )}
          <textarea
            className={styles.textarea}
            placeholder={placeholder}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={onKey}
            disabled={sending}
          />
          <button
            className={styles.send}
            type="button"
            onClick={doSend}
            disabled={sending || !value.trim()}
            aria-label="发送"
            title="发送"
          >
            Send
          </button>
        </div>
        <div className={styles.hint}>
          AI 可能会生成不准确的信息，请核实关键内容。
        </div>
      </div>
      <DocumentSnippetPreview
        snippetData={previewSnippet}
        isOpen={showPreview}
        onClose={closePreview}
      />
    </div>
  );
}
