<script setup lang="ts">
import axios from "axios";
import { ref, onMounted } from "vue";
import { jwtDecode } from "jwt-decode";

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
    const response = await axios.get(`http://localhost:8001/books/${book_id}`);
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
      `http://localhost:8001/books/status/book/${userInfo.user_id}`,
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
    if (error.response) {
      errorMessage.value = error.response.data.detail;
    } else {
      errorMessage.value = "Unexpected error: " + error.message;
    }
  } finally {
    loading.value = false;
  }
}

// Khi component mount
onMounted(async () => {
  await getCurrentlyReadingBooks();
});
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow border">
    <div v-if="loading">Đang tải...</div>
    <div v-else-if="errorMessage" class="text-red-500">
      {{ errorMessage }}
    </div>
    <div v-else>
      <h3 class="text-lg font-semibold mb-4">
        Currently reading ({{ books.length }})
      </h3>

      <div class="flex items-start space-x-4">
        <div
          v-for="item in books"
          :key="item.book.id"
          class="w-24 h-36 shadow-md flex items-center justify-center border rounded overflow-hidden"
        >
          <img
            :src="`http://34.9.73.53/uploads/${item.book.cover_url}`"
            alt="Book Cover"
            class="h-full w-full object-contain"
          />
        </div>
      </div>

      <div class="mt-4 flex space-x-3">
        <button
          class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm"
        >
          View all
        </button>
        <button
          class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm"
        >
          Reading Journal
        </button>
      </div>
    </div>
  </div>
</template>
