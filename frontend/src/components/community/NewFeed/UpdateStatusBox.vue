<script setup lang="ts">
import { ref, Ref } from "vue";
import axios from "axios";
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from "../../../config"; // Thêm COVER_IMAGE
import { useAuth } from "../../../composables/useAuth";
import { useBookSearch } from "../../../composables/useBookSearch";

const { userInfo } = useAuth();
const { query, results, searchBooks } = useBookSearch() as {
  query: Ref<string>;
  results: Ref<any[]>; // Dùng 'any' để linh hoạt
  searchBooks: () => Promise<void>;
};

interface Book {
  id: number;
  title: string;
  cover_url?: string;
}

const selectedBook = ref<Book | null>(null);
const isLoading = ref(false);
const message = ref("");

function handleSelectBook(book: Book) {
  selectedBook.value = book;
  query.value = book.title;
  results.value = []; // Ẩn kết quả
}

// Hàm này gọi API PUT /{book_id}/status mà bạn đã có trong books.py
async function updateStatus(status: 'currently_reading' | 'read' | 'to_read') {
  if (!selectedBook.value) return;

  const userId = userInfo.value?.id || userInfo.value?.user_id;
  const bookId = selectedBook.value.id;

  if (!userId) {
    message.value = "Lỗi: Không thể xác thực người dùng.";
    return;
  }

  isLoading.value = true;
  message.value = "Đang cập nhật...";

  try {
    // API này của bạn (books.py) nhận status và user_id qua query params
    await axios.put(
      `${BOOK_SERVICE_URL}books/${bookId}/status?user_id=${userId}&status=${status}`
    );

    message.value = "Cập nhật thành công!";
    
    // Reset component
    setTimeout(() => {
      selectedBook.value = null;
      query.value = "";
      message.value = "";
    }, 1500);

  } catch (err: any) {
    message.value = err.response?.data?.detail || "Lỗi khi cập nhật.";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="bg-white p-5 rounded-lg shadow border mb-8">
    
    <!-- Giai đoạn 1: Tìm kiếm -->
    <div v-if="!selectedBook">
      <label class="block text-sm font-medium text-gray-600 mb-1">Bạn đang đọc gì?</label>
      <input 
        v-model="query" 
        @input="searchBooks" 
        type="text" 
        class="w-full border rounded-md px-3 py-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
        placeholder="Tìm sách để cập nhật trạng thái..." 
      />
      <!-- Kết quả tìm kiếm -->
      <ul v-if="results.length" class="border rounded-md mt-2 bg-white shadow-sm max-h-48 overflow-y-auto z-10">
        <li 
          v-for="book in results" 
          :key="book.id" 
          @click="handleSelectBook(book)"
          class="px-3 py-2 hover:bg-yellow-50 cursor-pointer flex items-center gap-3"
        >
          <img 
            :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" 
            class="w-8 h-12 object-cover rounded" 
            alt="Bìa sách"
          />
          <span>{{ book.title }}</span>
        </li>
      </ul>
    </div>

    <!-- Giai đoạn 2: Cập nhật -->
    <div v-else>
      <p class="text-sm font-medium text-gray-600 mb-2">Cập nhật trạng thái cho:</p>
      <div class="flex gap-3 bg-gray-50 p-3 rounded-md">
        <img 
          :src="`${COVER_IMAGE_SERVER_URL}/${selectedBook.cover_url}`" 
          class="w-10 h-14 object-cover rounded" 
          alt="Bìa sách"
        />
        <p class="font-semibold text-gray-800">{{ selectedBook.title }}</p>
      </div>

      <div class="flex flex-wrap gap-3 mt-4">
        <button 
          @click="updateStatus('currently_reading')"
          :disabled="isLoading"
          class="px-3 py-1.5 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md text-sm"
        >
          Bắt đầu đọc
        </button>
        <button 
          @click="updateStatus('read')"
          :disabled="isLoading"
          class="px-3 py-1.5 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md text-sm"
        >
          Đã đọc xong
        </button>
        <button 
          @click="updateStatus('to_read')"
          :disabled="isLoading"
          class="px-3 py-1.5 bg-gray-200 hover:bg-gray-300 text-black font-semibold rounded-md text-sm"
        >
          Muốn đọc
        </button>
      </div>

      <p v-if="message" class="text-sm text-yellow-600 mt-3">{{ message }}</p>
    </div>
  </div>
</template>
