import { useState } from 'react';
import styles from './SignUp.module.css'
import { Link, useNavigate } from "react-router-dom";
import { register } from './api/user';
function SignUp() {
  const [newEmail,setNewEmail] = useState('')
  const [newPassword,setNewPassword] = useState('')
  const [userName,setUserName] = useState('')
  const nav = useNavigate()
    return (
      <div className={styles.container}>
        <div className={styles.title}>
          <h2 className={styles.titlehead}>注册</h2>
          <small className={styles.titleparagraph}>
            已有账户？<Link to="/">登录</Link>
          </small>
        </div>
        <div className={styles.in}>
          <input type="text" onChange={(e)=>setNewEmail(e.target.value)} className={styles.inputText} placeholder='email'/>
          <input type="text" onChange={(e)=>setUserName(e.target.value)} className={styles.inputText} placeholder='username'/>
          <input type="password" onChange={(e)=>setNewPassword(e.target.value)} className={styles.inputPassword} placeholder='password'/>
          <div>
            <label
              className={`${styles.titleparagraph} ${styles.checkbox}`}
              for="happy"
            >
              <input type="checkbox" id="happy" />我已阅读并同意协议
            </label>
          </div>
        </div>
        <div>
          <button onClick={()=>{
            register({"username":userName,"email":newEmail,"password":newPassword})
            nav(-1)
          }} className={styles.button}>注册</button>
        </div>
      </div>
    );
}

export default SignUp
