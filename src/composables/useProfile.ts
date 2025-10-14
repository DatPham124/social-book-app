import axios from "axios";
import { USER_SERVICE_URL } from "../config";

export async function getProfile(userId: number) {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(
      `${USER_SERVICE_URL}users/profile/${userId}`,
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    return response.data; 
  } catch (error) {
    console.error("Lỗi khi lấy dữ liệu người dùng:", error);
    return null;
  }
}
