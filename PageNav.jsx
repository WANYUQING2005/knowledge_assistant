import styles from './PageNav.module.css'
import { NavLink, useNavigate } from "react-router-dom";
import HomePage from './HomePage'
function PageNav() {
  const nav = useNavigate()
    return (
      <div className={styles.base}>
        <div
          onClick={() => {
            nav("/baselibrary");
          }}
        >
          {" "}
          控制台{" "}
        </div>
        <div onClick={()=>{}}>用户文档</div>
        <div
          onClick={() => {
            nav("/chat");
          }}
        >
          聊天
        </div>
      </div>
    );
}

export default PageNav
