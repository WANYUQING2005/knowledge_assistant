import { useEffect, useState } from 'react'
import Page1 from './assets/nahidaimg/2.jpg'
import Page2 from './assets/nahidaimg/3.jpg'
import Page3 from './assets/nahidaimg/4.jpg'
import Page4 from './assets/2.png'
import Page5 from './assets/3.png'
import Page6 from './assets/4.png'
import Page7 from './assets/5.png'
import styles from './TransformImages.module.css'
function TransformImages() {
    const pages = [Page4,Page5,Page6,Page7]
    const [index,setIndex] = useState(0)
    useEffect(()=>{
        const timer = setInterval(()=>{
            setIndex((index)=>index>=pages.length-1?0:index+1)
            
        },3000)
        return () => clearInterval(timer);
    },[])
    return (
        <div className={styles.imgContainer}>
            <img src = {pages[index]} alt='pages' className={styles.img}/>
        </div>
    )
}

export default TransformImages
