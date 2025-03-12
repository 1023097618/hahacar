// loadAMap.js
const key=process.env.VUE_APP_map_key
export function loadAMap() {
    return new Promise((resolve, reject) => {
      // 如果全局已存在 AMap 对象，说明已经加载过脚本，直接resolve
      if (typeof window !== 'undefined' && window.AMap) {
        resolve(window.AMap);
        return;
      }
  
      // 创建 script 标签
      const script = document.createElement('script');
      script.type = 'text/javascript';
      script.src = `https://webapi.amap.com/maps?v=2.0&key=${key}&plugin=AMap.ControlBar,AMap.ToolBar`;
  
      // 加载成功
      script.onload = () => {
        if (window.AMap) {
          resolve(window.AMap);
        } else {
          reject(new Error('高德地图脚本已加载，但未检测到 AMap 对象'));
        }
      };
  
      // 加载失败
      script.onerror = () => {
        reject(new Error('高德地图脚本加载失败'));
      };
  
      // 将 script 插入页面
      document.head.appendChild(script);
    });
  }
  