import AccountHeader from "./AccountHeader";
import logo from "./assets/newlogo.png";
import styles from "./Header.module.css";
import PageNav from "./PageNav";

function Header() {
  return (
    <div className={styles.container}>
      <header className={styles.head}>
        <div className={styles.logoandnav}>
          <div className={styles.logoandword}>
            <img src={logo} alt="logo" className={styles.logo} />
            <h1 className={styles.h1}>个人知识库助手</h1>
          </div>
          <PageNav />
        </div>
        <AccountHeader />
      </header>
    </div>
  );
}

export default Header;
