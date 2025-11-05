<script setup lang="ts">
import axios from "axios";
import { ref, onMounted } from "vue";
import { jwtDecode } from "jwt-decode";
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from "../../config.ts"; // import config

const books = ref<any[]>([]);
const loading = ref(true);
const errorMessage = ref<string | null>(null);

interface TokenPayLoad {
  username: string;
  roles: number[];
  exp: number;
  user_id: number;
  id: number;
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

async function get_book_by_id(book_id: number) {
  try {
    const response = await axios.get(`${BOOK_SERVICE_URL}books/${book_id}`);
    return response.data;
  } catch (error: any) {
    console.error("Error fetching book detail", error);
    return null;
  }
}

async function getToReadBooks() {
  if (!userInfo) {
    errorMessage.value = "Bạn chưa đăng nhập!";
    loading.value = false;
    return;
  }
  
  const userId = userInfo.user_id || userInfo.id;

  try {
    const response = await axios.get(
      `${BOOK_SERVICE_URL}books/status/book/${userId}`,
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
        // API trả về 404 (đã sửa) nghĩa là không có sách, gán mảng rỗng
        books.value = []; 
      } else {
        errorMessage.value = "Đã xảy ra lỗi.";
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
  <!-- 1. Thêm flex flex-col để xử lý chiều cao h-[325px] từ cha -->
  <div class="bg-white p-6 rounded-lg shadow border h-full flex flex-col">
    <h3 class="text-lg font-semibold mb-4">Sẽ đọc ({{ books.length }})</h3>

    <!-- 2. Thêm flex-1 overflow-y-auto để nội dung cuộn -->
    <div class="flex-1 overflow-y-auto">
      <div v-if="loading" class="text-gray-500 italic">Đang tải...</div>
      
      <!-- 3. Sửa logic hiển thị lỗi/trống -->
      <div v-else-if="errorMessage" class="text-gray-500 italic">
        {{ errorMessage }}
      </div>
      <div v-else-if="books.length === 0" class="text-gray-500 italic">
        Bạn chưa có sách nào trong mục Sẽ đọc.
      </div>
      
      <!-- 4. Danh sách (chỉ hiển thị khi có sách) -->
      <div v-else>
        <ul class="divide-y divide-gray-200">
          <li v-for="item in books.slice(0, 3)" :key="item.book.id" class="py-2">
            <router-link :to="{ name: 'book', params: { id: item.book.id } }">

              <p class="text-gray-800 font-medium truncate">
                {{ item.book.title }}
              </p>
            </router-link>
            <p class="text-gray-500 text-sm">
              {{ item.book.author || "Không rõ tác giả" }}
            </p>
          </li>
        </ul>
      </div>
    </div>

    <!-- 5. Thêm v-if vào nút "Xem tất cả" -->
    <div v-if="!loading && !errorMessage && books.length > 0" class="mt-4 text-center">
      <router-link :to="{ name: 'view_all_to_read_book' }"
        class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm shadow">
        Xem tất cả
      </router-link>
    </div>
  </div>
</template>
