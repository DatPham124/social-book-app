import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

// Lấy thông tin từ code bạn cung cấp
const firebaseConfig = {
    apiKey: "AIzaSyBBwx33GoMKb1PgXgTsdxJDL9YQmTHAz1I",
    authDomain: "realtime-6cee8.firebaseapp.com",
    projectId: "realtime-6cee8",
    storageBucket: "realtime-6cee8.firebasestorage.app",
    messagingSenderId: "680063110664",
    appId: "1:680063110664:web:75de42784c4d3a79828bbd"
};

// Khởi tạo 1 lần duy nhất
const firebaseApp = initializeApp(firebaseConfig);
const db = getFirestore(firebaseApp);

// Xuất ra để các nơi khác dùng
export { firebaseApp, db };