<script setup lang="ts">
import { ref, onMounted } from "vue";
import { jwtDecode } from "jwt-decode";
import { useBooks } from "../../composables/useBook.ts";
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from "../../config.ts";

import BookProgress from "../../components/books/BookProgress.vue";
import BookStatusSelect from "../../components/books/BookStatusSelect.vue";

const {
  fetchBook,
  fetchBooksByStatus,
  formatDate
} = useBooks();

const props = withDefaults(
  defineProps<{
    status?: "to_read" | "currently_reading" | "read" | "dnf" | "rm_book";
    title?: string;
  }>(),
  {
    status: "to_read",
  }
);


const books = ref<any[]>([]);
const loading = ref(true);
const errorMessages = ref("");

const statuses = [
  { value: "to_read", label: "Sẽ đọc" },
  { value: "currently_reading", label: "Đang đọc" },
  { value: "read", label: "Đã đọc" },
  { value: "dnf", label: "Chưa hoàn thành" },
];

let userInfo: any = null;
const token = localStorage.getItem("token");
if (token) {
  try {
    userInfo = jwtDecode<any>(token);
    if (userInfo.exp * 1000 < Date.now()) {
      localStorage.removeItem("token");
      userInfo = null;
    }
  } catch {
    localStorage.removeItem("token");
  }
}

function mapStatus(statusStr: string) {
  return statuses.find((s) => s.value === statusStr) || statuses[0];
}

async function updateBookStatus(bookId: number, newStatus: any) {
  try {
    await fetch(`${BOOK_SERVICE_URL}books/${bookId}/status?user_id=${userInfo.user_id}&status=${newStatus.value}`, {
      method: "PUT",
    });
    await fetchBooks();
  } catch (error) {
    console.error("Lỗi khi cập nhật trạng thái:", error);
  }
}

async function fetchBooks() {
  if (!userInfo) {
    errorMessages.value = "Vui lòng đăng nhập để xem danh sách";
    loading.value = false;
    return;
  }

  try {
    loading.value = true;

    const userBooks = await fetchBooksByStatus(userInfo.user_id, props.status);

    const results = await Promise.all(
      userBooks.map(async (userBook: any) => {
        const detail = await fetchBook(userBook.book_id, userInfo.user_id);
        if (!detail) return null;
        return {
          ...detail,
          start_date: userBook.start_date,
          status: mapStatus(userBook.status),
          editingProgress: false,
          newPage: detail.current_page,
        };
      })
    );

    books.value = results.filter(Boolean);
  } catch (error) {
    console.error(error);
    errorMessages.value = "Không thể tải danh sách sách";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchBooks);
</script>

<template>
  <div class="max-w-3xl mx-auto p-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-logo text-yellow-400">{{ props.title }}</h1>

      <router-link v-if="props.status === 'currently_reading'" to="/reading-journal"
        class="px-4 py-1 rounded-md border bg-white hover:bg-yellow-200 text-sm">
        Xem nhật ký
      </router-link>
    </div>

    <p class="text-gray-500 text-sm mb-6">{{ books.length }} sách</p>

    <div v-if="loading" class="text-center py-8 text-gray-500">Đang tải sách...</div>
    <div v-else-if="errorMessages" class="text-center py-8 text-red-500">{{ errorMessages }}</div>

    <div v-else-if="books.length === 0" class="text-center py-8 text-gray-500">
      Không có sách nào
      <router-link to="/explore" class="text-yellow-500 hover:text-yellow-600 ml-1">
        Khám phá sách mới →
      </router-link>
    </div>

    <div v-else>
      <div v-for="(book, index) in books" :key="book.id" class="flex border rounded-xl shadow-sm mb-6 bg-white">
        <!-- Ảnh bìa -->
        <div class="w-32 h-52 flex-shrink-0">
          <router-link :to="{ name: 'book', params: { id: book.id } }" class="w-32 h-52 flex-shrink-0 block">
            <img :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" :alt="book.title"
              class="w-full h-full object-cover rounded-l-xl cursor-pointer" />
          </router-link>
        </div>

        <div class="flex flex-grow p-4">
          <div class="flex-grow pr-6 border-r border-gray-100 min-w-0">
            <router-link
            :to="{ name: 'book', params: { id: book.id } }"
            class="font-bold text-lg mb-0.5 text-gray-800 hover:text-yellow-600 transition"
            >
            {{ book.title }}
            </router-link>
            <p class="text-gray-600 text-sm mb-1">{{ book.author }}</p>
            <p class="text-gray-500 text-xs mb-3">
              {{ book.page_count }} trang • {{ book.language }} •
              {{ new Date(book.published_date).getFullYear() }}
            </p>

            <div class="flex flex-wrap gap-2 mb-4">
              <span v-for="category in book.categories" :key="category"
                class="px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full text-xs font-medium">
                {{ category }}
              </span>
            </div>

            <p class="text-xs text-gray-500 mt-auto">
              Bắt đầu đọc: {{ formatDate(book.start_date) }}
            </p>
          </div>

          <div class="w-56 pl-6 flex flex-col justify-between items-start flex-shrink-0">
            <BookProgress v-if="props.status === 'currently_reading'" :book="book" :userId="userInfo.user_id"
              @update="(updatedBook) => (books[index] = updatedBook)" />

            <BookStatusSelect v-model="book.status" :bookId="book.id" :userId="userInfo.user_id" class="mt-3" />

            <div class="flex flex-col gap-2 w-full mt-auto">
              <button @click="updateBookStatus(book.id, { value: 'read' })"
                class="text-sm text-yellow-600 hover:text-yellow-700 font-medium text-left"
                v-if="props.status === 'currently_reading'">
                → Đánh dấu "Đã đọc"
              </button>
              <button @click="updateBookStatus(book.id, { value: 'dnf' })"
                class="text-sm text-gray-500 hover:text-gray-700 text-left" v-if="props.status === 'currently_reading'">
                → Đánh dấu "Chưa hoàn thành"
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
