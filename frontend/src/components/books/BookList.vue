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
  { value: "rm_book", label: "Xóa sách khỏi kệ" },
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
    <div class="flex justify-between items-end mb-6">
      <p class="text-gray-500 text-sm font-medium">{{ books.length }} quyển sách</p>
      </div>

    <div v-if="loading" class="text-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-500 mx-auto mb-2"></div>
      <span class="text-gray-500">Đang tải sách...</span>
    </div>

    <div v-else-if="errorMessages" class="text-center py-8 text-red-500">{{ errorMessages }}</div>

    <div v-else-if="books.length === 0" class="text-center py-16 bg-gray-50 rounded-xl border border-dashed border-gray-300">
      <p class="text-gray-500 mb-2">Chưa có sách nào trong danh sách này</p>
      <router-link to="/explore" class="text-yellow-600 font-medium hover:underline hover:text-yellow-700">
        Khám phá sách mới →
      </router-link>
    </div>

    <div v-else class="space-y-6">
      <div v-for="(book, index) in books" :key="book.id" 
           class="flex flex-col sm:flex-row bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200">
        
        <div class="w-full sm:w-32 h-48 sm:h-auto flex-shrink-0 relative bg-gray-100">
          <router-link :to="{ name: 'book', params: { id: book.id } }" class="block w-full h-full">
            <img 
              :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" 
              :alt="book.title"
              class="w-full h-full object-cover" 
            />
          </router-link>
        </div>

        <div class="flex flex-col flex-grow p-4 sm:p-5">
          
          <div class="flex justify-between items-start gap-4 mb-2">
            <div>
              <router-link
                :to="{ name: 'book', params: { id: book.id } }"
                class="font-bold text-lg text-gray-800 hover:text-yellow-600 line-clamp-2 leading-tight"
              >
                {{ book.title }}
              </router-link>
              <p class="text-gray-600 text-sm mt-1">{{ book.author }}</p>
            </div>

            <div class="flex-shrink-0">
               <BookStatusSelect 
                  v-model="book.status" 
                  :bookId="book.id" 
                  :userId="userInfo.user_id"
                  class="min-w-[140px]" 
               />
            </div>
          </div>

          <p class="text-gray-500 text-xs mb-3">
            {{ book.page_count }} trang • {{ book.language }} • {{ new Date(book.published_date).getFullYear() }}
          </p>

          <div class="flex flex-wrap gap-2 mb-4">
            <span v-for="category in book.categories" :key="category"
              class="px-2.5 py-0.5 bg-yellow-50 text-yellow-700 border border-yellow-100 rounded-full text-xs font-medium">
              {{ category }}
            </span>
          </div>

          <div class="mt-auto pt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <p class="text-xs text-gray-400">
              <span v-if="book.start_date">Bắt đầu: {{ formatDate(book.start_date) }}</span>
            </p>

            <div v-if="props.status === 'currently_reading'" class="w-full sm:w-1/2">
               <BookProgress 
                  :book="book" 
                  :userId="userInfo.user_id"
                  @update="(updatedBook) => (books[index] = updatedBook)" 
               />
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>
