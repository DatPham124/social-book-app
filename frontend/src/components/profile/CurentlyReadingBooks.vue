<script setup lang="ts">
import axios from "axios";
import { ref, onMounted, watch } from "vue"; // Thêm watch
import { jwtDecode } from "jwt-decode";
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from "../../config.ts";
import { useBooks } from "../../composables/useBook.ts";


// 1. Định nghĩa Props nhận từ cha
const props = defineProps<{
    userID?: number | string;
}>();

const { getBookById, errorMessage } = useBooks();
const books = ref<any[]>([]);
const loading = ref(true);

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

async function getCurrentlyReadingBooks() {
  loading.value = true; // Reset loading khi gọi lại hàm

  // 2. Logic chọn ID: Ưu tiên props từ cha, nếu không có thì lấy của chính mình
  const targetID = props.userID ? Number(props.userID) : userInfo?.user_id;

  if (!targetID) {
    // Nếu cả props và userInfo đều không có -> Chưa đăng nhập và không xem profile ai
    errorMessage.value = "Không xác định được người dùng.";
    loading.value = false;
    return;
  }

  try {
    const response = await axios.get(
      `${BOOK_SERVICE_URL}books/status/book/${targetID}`, // Dùng targetID
      {
        params: { status: "currently_reading" },
      }
    );

    const statusList = response.data;

    const detailedBooks = await Promise.all(
      statusList.map(async (item: any) => {
        const book = await getBookById(item.book_id);
        return { ...item, book };
      })
    );

    books.value = detailedBooks.filter((b) => b.book !== null);

    if (books.value.length === 0) {
      errorMessage.value = "Chưa có sách nào trong mục Đang đọc.";
    } else {
        errorMessage.value = null; // Xóa lỗi cũ nếu có
    }
  } catch (error: any) {
    if (axios.isAxiosError(error) && error.response) {
      if (error.response.status === 404) {
        errorMessage.value = "Chưa có sách nào trong mục Đang đọc.";
      } else if (error.response.status === 400) {
        errorMessage.value = "Yêu cầu không hợp lệ.";
      } else {
        errorMessage.value = "Đã xảy ra lỗi.";
      }
    } else {
      errorMessage.value = "Không thể kết nối đến server.";
    }
    books.value = []; // Reset sách nếu lỗi
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await getCurrentlyReadingBooks();
});

// 3. Theo dõi sự thay đổi của userID để load lại dữ liệu
watch(() => props.userID, () => {
    getCurrentlyReadingBooks();
});
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow border h-[325px] flex flex-col">
    <h3 class="text-lg font-semibold mb-4">
      Đang đọc ({{ books.length }})
    </h3>

    <div class="flex-1 flex flex-col justify-center">
      <div v-if="loading" class="text-center text-gray-500">Đang tải...</div>
      <div v-else-if="errorMessage" class="text-gray-500 italic text-center">
        {{ errorMessage }}
      </div>
      <div v-else class="space-y-10">
        <div class="flex space-x-4 justify-center">
          <div v-for="item in books.slice(0, 4)" :key="item.book.id"
            class="w-20 h-28 shadow rounded overflow-hidden bg-gray-100 flex">
            <router-link :to="{ name: 'book', params: { id: item.book.id } }">
              <img v-if="item.book.cover_url" :src="`${COVER_IMAGE_SERVER_URL}/${item.book.cover_url}`"
                :alt="item.book.title" class="h-full w-full object-cover" />
            </router-link>
          </div>
        </div>

        <div class="mt-4 flex space-x-3 justify-center">
           <!-- Bạn có thể cần sửa router-link này để truyền thêm params id người đang xem -->
          <router-link to="/profile/view/curently" class="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 text-sm">
            Xem tất cả
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>