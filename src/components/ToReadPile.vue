<script setup lang="ts">
import axios from "axios";
import { ref, onMounted } from "vue";
import { jwtDecode } from "jwt-decode";
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from "../config.ts"; // import config

const books = ref<any[]>([]);
const loading = ref(true);
const errorMessage = ref<string | null>(null);

interface TokenPayLoad {
  username: string;
  roles: number[];
  exp: number;
  user_id: number;
}

const token = localStorage.getItem("token");
let userInfo: TokenPayLoad | null = null;

if (token) {
  try {
    userInfo = jwtDecode<TokenPayLoad>(token);
    if (userInfo.exp * 1000 < Date.now()) {
      localStorage.removeItem("token");
      userInfo = null;
    }
  } catch (error) {
    console.error("Invalid token:", error);
    localStorage.removeItem("token");
  }
}

// API: lấy chi tiết 1 cuốn sách
async function get_book_by_id(book_id: number) {
  try {
    const response = await axios.get(`${BOOK_SERVICE_URL}books/${book_id}`);
    return response.data;
  } catch (error: any) {
    console.error("Error fetching book detail", error);
    return null;
  }
}

// API: lấy danh sách "to_read"
async function getToReadBooks() {
  if (!userInfo) {
    errorMessage.value = "Bạn chưa đăng nhập!";
    loading.value = false;
    return;
  }

  try {
    const response = await axios.get(
      `${BOOK_SERVICE_URL}books/status/book/${userInfo.user_id}`,
      { params: { status: "to_read" } }
    );

    const statusList = response.data;

    const detailedBooks = await Promise.all(
      statusList.map(async (item: any) => {
        const book = await get_book_by_id(item.book_id);
        return { ...item, book };
      })
    );

    books.value = detailedBooks.filter((b) => b.book !== null);
  } catch (error: any) {
    if (axios.isAxiosError(error) && error.response) {
      if (error.response.status === 404) {
        // Trường hợp không tìm thấy sách
        errorMessage.value = "Bạn chưa có sách nào trong mục Sẽ đọc.";
      } else if (error.response.status === 400) {
        errorMessage.value = "Yêu cầu không hợp lệ. Vui lòng thử lại.";
      } else {
        errorMessage.value = "Đã xảy ra lỗi. Vui lòng thử lại sau.";
      }
    } else {
      errorMessage.value = "Không thể kết nối đến server.";
    }
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  getToReadBooks();
});
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow border">
    <h3 class="text-lg font-semibold mb-4">Sẽ đọc ({{ books.length }})</h3>

    <div v-if="loading">Đang tải...</div>
    <div v-else-if="errorMessage" class="text-gray-500 italic">
      {{ errorMessage }}
    </div>
    <div v-else>
      <div class="flex space-x-4">
        <div v-for="item in books" :key="item.book.id"
          class="w-20 h-28 shadow rounded overflow-hidden bg-gray-100 flex items-center justify-center">
          <img v-if="item.book.cover_url" :src="`${COVER_IMAGE_SERVER_URL}/${item.book.cover_url}`" :alt="item.book.title"
            class="h-full w-full object-cover" />
          <span v-else class="text-xs text-gray-500 p-1 text-center">
            {{ item.book.title }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
