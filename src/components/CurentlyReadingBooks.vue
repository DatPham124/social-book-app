<script setup lang="ts">
import axios from "axios";
import { ref, onMounted } from "vue";
import { jwtDecode } from "jwt-decode";
import { BOOK_SERVICE_URL, IMAGE_SERVER_URL } from "../config.ts";

// State
const books = ref<any[]>([]); // mảng sách chi tiết
const loading = ref(true);
const errorMessage = ref<string | null>(null);

// Interface token
interface TokenPayLoad {
  username: string;
  roles: number[];
  exp: number;
  user_id: number;
}

// Lấy userInfo từ token
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
    return response.data; // dữ liệu chi tiết sách
  } catch (error: unknown) {
    if (axios.isAxiosError(error) && error.response) {
      errorMessage.value = error.response.data.detail;
    } else {
      errorMessage.value = "Không thể kết nối đến server";
    }
    return null;
  }
}

// API: lấy danh sách currently reading và map sang chi tiết sách
async function getCurrentlyReadingBooks() {
  if (!userInfo) {
    errorMessage.value = "Bạn chưa đăng nhập!";
    loading.value = false;
    return;
  }

  try {
    const response = await axios.get(
      `${BOOK_SERVICE_URL}books/status/book/${userInfo.user_id}`,
      {
        params: { status: "currently_reading" },
      }
    );

    const statusList = response.data;

    const detailedBooks = await Promise.all(
      statusList.map(async (item: any) => {
        const book = await get_book_by_id(item.book_id);
        return { ...item, book };
      })
    );

    books.value = detailedBooks.filter((b) => b.book !== null); // loại bỏ null
  } catch (error: any) {
    if (axios.isAxiosError(error) && error.response) {
      if (error.response.status === 404) {
        errorMessage.value = "Bạn chưa có sách nào trong mục Đang đọc.";
      } else if (error.response.status === 400) {
        errorMessage.value = "Yêu cầu không hợp lệ. Vui lòng thử lại.";
      } else {
        errorMessage.value = "Đã xảy ra lỗi. Vui lòng thử lại sau.";
      }
    } else {
      errorMessage.value = "Không thể kết nối đến server.";
    }
  } finally {
    loading.value = false
  }

}

// Khi component mount
onMounted(async () => {
  await getCurrentlyReadingBooks();
});
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow border">
    <h3 class="text-lg font-semibold mb-4">Đang đọc ({{ books.length }})</h3>

    <div v-if="loading">Đang tải...</div>
    <div v-else-if="errorMessage" class="text-gray-500 italic">
      {{ errorMessage }}
    </div>

    <div v-else>
      <h3 class="text-lg font-semibold mb-4">
        Currently reading ({{ books.length }})
      </h3>

      <div class="flex items-start space-x-4">
        <div v-for="item in books" :key="item.book.id"
          class="w-24 h-36 shadow-md flex items-center justify-center rounded overflow-hidden">
          <img :src="`${IMAGE_SERVER_URL}/${item.book.cover_url}`" :alt="item.book.title"
            class="h-full w-full object-contain" />
        </div>
      </div>

      <div class="mt-4 flex space-x-3">
        <button class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm">
          View all
        </button>
        <button class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm">
          Reading Journal
        </button>
      </div>
    </div>
  </div>
</template>
