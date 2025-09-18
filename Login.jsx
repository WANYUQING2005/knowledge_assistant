import { Link, Navigate, useNavigate } from 'react-router-dom';
import styles from './Login.module.css'
import { useState } from 'react';
import { login } from './api/user';
function Login() {
    // const [success,setSuccess] = useState(false)
    const [userName,setUserName] = useState('')
    const [password,setPassword]=useState('')
    const nav = useNavigate()
    const  check = async (e)=>{
      const response = await login({"username":userName,"password":password})
      const {status,token,user_id} = response.data
      if(status==='success')
      {
        localStorage.setItem("token",token)
        localStorage.setItem("user_id",user_id)
        nav('baselibrary')
      }
    }
    return (
      <div className={styles.container}>
        <div className={styles.title}>
          <h2 className={styles.titlehead}>登录</h2>
          <small className={styles.titleparagraph}>
            没有帐户？ <Link to="signup"> 注册</Link>
          </small>
        </div>
        <div className={styles.in}>
          <input
            type="text"
            onChange={(e) => setUserName(e.target.value)}
            className={styles.inputText}
            placeholder="username"
          />
          <input
            type="password"
            onChange={(e) => setPassword(e.target.value)}
            className={styles.inputPassword}
            placeholder="password"
          />
          <div>
            <label
              className={`${styles.titleparagraph} ${styles.checkbox}`}
            
            >
              <input type="checkbox" id="happy" />我已阅读并同意协议
            </label>
            <label
              className={`${styles.titleparagraph} ${styles.checkbox}`}
              
            >
              <input type="checkbox" id="happy1" />
              记住密码
            </label>
          </div>
        </div>
        <div>
          <button onClick={check} className={styles.button}>
            登录
          </button>
        </div>
      </div>
    );
}

export default Login
