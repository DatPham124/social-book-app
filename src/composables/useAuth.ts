import { ref } from "vue";
import { jwtDecode } from "jwt-decode";

export function useAuth() {
  const userInfo = ref<any>(null);

  function loadUserFromToken() {
    const token = localStorage.getItem("token");
    if (!token) {
      userInfo.value = null;
      return null;
    }

    try {
      const decoded = jwtDecode<any>(token);

      if (decoded.exp * 1000 < Date.now()) {
        localStorage.removeItem("token");
        userInfo.value = null;
        return null;
      }

      userInfo.value = decoded;
      return decoded;
    } catch (error) {
      localStorage.removeItem("token");
      userInfo.value = null;
      return null;
    }
  }

  loadUserFromToken();

  return {
    userInfo,
    loadUserFromToken,
  };
}
