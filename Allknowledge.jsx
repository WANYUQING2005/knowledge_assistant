import { useEffect, useState } from "react";
import styles from "./Allknowledge.module.css";
import Table from "./Table";
import Modal from "./Modal";
import Back from "./Back";
import { listKnowledge } from "./api/user";
function Allknowledge() {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const id = localStorage.getItem("user_id");
  const [pages, setPages] = useState([]);
  const refresh = async () => {
    try {
      const res = await listKnowledge(id);
      setPages(res.data || []);
    } catch (error) {
      console.error("加载知识库失败:", error);
      setPages([]);
    }
  };
  useEffect(() => {
    refresh();
  }, []);
  return (
    <div className={styles.main}>
      <div className={styles.header}>
        <div className={styles.first}>
          <Back />
          <h2 className={styles.title}>知识库</h2>
        </div>
        <button className={styles.btn} onClick={() => setOpen(true)}>
          + 创建新知识库
        </button>
      </div>

      <hr className={styles.hr} />

      <div className={styles.libraries}>
        <Table pages={pages} setPages={setPages} />
      </div>

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        refresh={refresh}
        title="新建知识库"
        name={name}
        description={description}
        setName={setName}
        setDescription={setDescription}
      >
        <div style={{ display: "grid", gap: 12, overflow: "hidden" }}>
          <label>
            知识库名称*
            <input
              placeholder="请输入知识库标题"
              style={{
                width: "90%",
                padding: "8px 10px",
                border: "1px solid #e5e7eb",
                borderRadius: 8,
              }}
              onChange={(e) => setName(e.target.value)}
            />
          </label>

          <label>
            向量化模型维度*
            <select
              style={{
                width: "90%",
                padding: "8px 10px",
                border: "1px solid #e5e7eb",
                borderRadius: 8,
              }}
            >
              <option>1024</option>
              <option>512</option>
              <option>256</option>
              <option>128</option>
            </select>
          </label>

          <label>
            知识库描述
            <textarea
              rows={3}
              placeholder="可选"
              style={{
                width: "90%",
                padding: "8px 10px",
                border: "1px solid #e5e7eb",
                borderRadius: 8,
              }}
              onChange={(e) => setDescription(e.target.value)}
            />
          </label>
        </div>
      </Modal>
    </div>
  );
}

export default Allknowledge;
