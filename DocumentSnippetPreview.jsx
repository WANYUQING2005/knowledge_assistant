import { useState } from "react";
import styles from "./DocumentSnippetPreview.module.css";
function DocumentSnippetPreview({ snippetData, onClose, isOpen }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    if (snippetData?.snippet) {
      try {
        await navigator.clipboard.writeText(snippetData.snippet);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      } catch (err) {
        console.error("复制失败:", err);
      }
    }
  };
  const formatSnippet = (snippet) => {
    if (!snippet) return "";
    return snippet
      .replace(/\n/g, "<br>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`(.*?)`/g, "<code>$1</code>");
  };

  const getScoreColor = (score) => {
    if (score >= 1.0) return "#10b981";
    if (score >= 0.7) return "#f59e0b"; 
    return "#ef4444"; 
  };

  const getScoreText = (score) => {
    if (score >= 1.0) return "高相关度";
    if (score >= 0.7) return "中等相关度";
    return "低相关度";
  };
  if (!isOpen || !snippetData) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.titleSection}>
            <h2 className={styles.title}>{snippetData.title || "文档片段"}</h2>
            <div className={styles.meta}>
              <span
                className={styles.score}
                style={{ color: getScoreColor(snippetData.score) }}
              >
                {getScoreText(snippetData.score)} (
                {snippetData.score?.toFixed(2)})
              </span>
              {snippetData.source && (
                <span className={styles.source}>
                  来源: {snippetData.source.split("/").pop()}
                </span>
              )}
            </div>
          </div>
          <div className={styles.actions}>
            <button
              className={styles.copyBtn}
              onClick={handleCopy}
              title="复制片段内容"
            >
              {copied ? "已复制" : "复制"}
            </button>
            <button className={styles.closeBtn} onClick={onClose}>
              ×
            </button>
          </div>
        </div>
        <div className={styles.content}>
          <div className={styles.snippetContent}>
            <div className={styles.label}>相关内容片段：</div>
            <div
              className={styles.snippet}
              dangerouslySetInnerHTML={{
                __html: formatSnippet(snippetData.snippet),
              }}
            />
          </div>
          {snippetData.kb_id && (
            <div className={styles.footer}>
              <span className={styles.kbId}>知识库ID: {snippetData.kb_id}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DocumentSnippetPreview;
