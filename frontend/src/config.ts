const ip = window.location.hostname;

export const USER_SERVICE_URL = `http://${ip}:8000/`;
export const BOOK_SERVICE_URL = `http://${ip}:8001/`;
export const REVIEW_SERVICE_URL = `http://${ip}:8002/`;

export const COVER_IMAGE_SERVER_URL = `http://${ip}/uploads/books`;
export const AVATAR_SERVER_URL = `http://${ip}/uploads/avatars`;
export const BOOKCLUB_IMAGE_SERVER_URL = `http://${ip}/uploads/bookclubs`;
export const AUDIO_SERVER_URL = `http://${ip}/uploads/audio`;
export const EBOOK_SERVER_URL = `http://${ip}/uploads/ebooks`;
