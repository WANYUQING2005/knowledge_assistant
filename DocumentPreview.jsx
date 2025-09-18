import { useState, useEffect } from "react";
import { getDocumentDetail } from "./api/documents";
import styles from "./DocumentPreview.module.css";

function DocumentPreview({ documentId, onClose, isOpen }) {
  const [document, setDocument] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && documentId) {
      loadDocumentDetail();
    }
  }, [isOpen, documentId]);
  const loadDocumentDetail = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log("Loading document detail for ID:", documentId);
      console.log("Document ID type:", typeof documentId);
      console.log("Document ID length:", documentId?.length);
      const response = await getDocumentDetail(documentId);
      console.log("Document detail API response:", response);
      if (response.data) {
        setDocument(response.data);
        console.log("Document loaded successfully:", response.data);
      } else {
        console.warn("No data in response:", response);
        setError("未获取到文档数据");
      }
    } catch (err) {
      console.error("Failed to load document detail:", err);
      console.error("Error details:", {
        message: err.message,
        response: err.response?.data,
        status: err.response?.status,
        config: err.config,
      });

      let errorMessage = "加载文档详情失败";
      if (err.response?.status === 404) {
        errorMessage = "文档不存在或已被删除";
      } else if (err.response?.status === 403) {
        errorMessage = "没有权限访问此文档";
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
      } else if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };
  const formatContent = (content) => {
    if (!content) return "";
    return content
      .replace(/\n/g, "<br>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/`(.*?)`/g, "<code>$1</code>");
  };

  if (!isOpen) return null;

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <div className={styles.titleSection}>
            <h2 className={styles.title}>{document?.title || "文档预览"}</h2>
            {document && (
              <div className={styles.meta}>
                <span className={styles.fileType}>{document.file_type}</span>
                <span className={styles.createTime}>
                  {new Date(document.create_at).toLocaleString()}
                </span>
              </div>
            )}
            {process.env.NODE_ENV === "development" && (
              <div className={styles.debugId}>文档ID: {documentId}</div>
            )}
          </div>
          <button className={styles.closeBtn} onClick={onClose}>
            ×
          </button>
        </div>

        <div className={styles.content}>
          {loading ? (
            <div className={styles.loading}>
              <div className={styles.spinner}></div>
              <span>加载中...</span>
              <div
                style={{ fontSize: "12px", color: "#999", marginTop: "8px" }}
              >
                文档ID: {documentId}
              </div>
            </div>
          ) : error ? (
            <div className={styles.error}>
              <span>{error}</span>
              <div
                style={{ fontSize: "12px", color: "#999", marginTop: "8px" }}
              >
                文档ID: {documentId}
              </div>
              <button onClick={loadDocumentDetail} className={styles.retryBtn}>
                重试
              </button>
            </div>
          ) : document ? (
            <div className={styles.documentContent}>
              {document.content ? (
                <div
                  className={styles.textContent}
                  dangerouslySetInnerHTML={{
                    __html: formatContent(document.content),
                  }}
                />
              ) : (
                <div className={styles.noContent}>暂无内容预览</div>
              )}

              {document.chunk_count && (
                <div className={styles.stats}>
                  <span>共 {document.chunk_count} 个文档块</span>
                </div>
              )}
            </div>
          ) : (
            <div className={styles.noDocument}>未找到文档信息</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DocumentPreview;
