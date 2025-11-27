// Tự động lấy IP hiện tại (localhost hoặc 192.168.x.x)
const ip = window.location.hostname;

// --- KIỂM TRA IP (Mở F12 -> Console để xem) ---
console.log("🌍 Current IP detected:", ip); 
// ----------------------------------------------

// Các Service API
export const USER_SERVICE_URL = `http://${ip}:8000/`;
export const BOOK_SERVICE_URL = `http://${ip}:8001/`;
export const REVIEW_SERVICE_URL = `http://${ip}:8002/`;

// File Server (Mặc định cổng 80 trên Linux/Nginx)
export const COVER_IMAGE_SERVER_URL = `http://${ip}/uploads/books`;
export const AVATAR_SERVER_URL = `http://${ip}/uploads/avatars`;
export const BOOKCLUB_IMAGE_SERVER_URL = `http://${ip}/uploads/bookclubs`;
export const AUDIO_SERVER_URL = `http://${ip}/uploads/audio`;