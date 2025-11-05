<script setup lang="ts">
import Navbar from '../components/layout/Navbar.vue';
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL, AVATAR_SERVER_URL } from '../config';
import { useAuth } from '../composables/useAuth';
import { getProfile } from '../composables/useProfile';
import { useBooks } from '../composables/useBook'; // <-- 1. SỬA LỖI IMPORT (thành 'useBook')
import BookStatusSelect from '../components/books/BookStatusSelect.vue'; 

const { userInfo } = useAuth();
const router = useRouter();
const { getUserBookStatus } = useBooks(); // <-- 2. SỬA LỖI (dùng useBooks())

// === State ===
const isOpen = ref(false);
const loading = ref(true);
const results = ref<any[]>([]);
const error = ref<string | null>(null);
const hasFiltered = ref(false);

const filters = ref({
  genres_include: "",
  genres_exclude: "",
  page_min: null as number | null,
  page_max: null as number | null,
  year_min: null as number | null,
  year_max: null as number | null,
  user_id_to_exclude_books: true,
});

// 3. SỬA MAP (thêm 'add_book' cho trạng thái rỗng)
const statusMap = {
  add_book: "Thêm vào kệ", // <-- Trạng thái mới
  to_read: "Sẽ đọc",
  currently_reading: "Đang đọc",
  read: "Đã đọc",
  dnf: "Chưa hoàn thành",
};

// === API Functions ===

async function fetchBookDetails(books: any[]) {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  
  const booksWithDetails = await Promise.all(
    books.map(async (book: any) => {
      const [profile, statusResult] = await Promise.all([
        getProfile(book.authorID), 
        // 4. API (đã sửa ở backend) giờ trả về NULL nếu không tìm thấy
        userId ? getUserBookStatus(userId, book.id) : null 
      ]);
      
      // 5. Logic xử lý NULL
      const statusKey = statusResult?.status || 'add_book'; // <-- Nếu NULL, dùng 'add_book'
      const statusObject = {
        value: statusKey,
        label: statusMap[statusKey as keyof typeof statusMap] || "Thêm vào kệ"
      };
      
      return { 
        ...book, 
        authorName: profile?.username || "Không rõ tác giả",
        statusObject: statusObject, // Gán object
        categories: book.categories || []
      };
    })
  );
  return booksWithDetails;
}

async function loadInitialExplore() {
  hasFiltered.value = false;
  loading.value = true;
  error.value = null;
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId) {
    error.value = "Không thể xác thực người dùng.";
    loading.value = false;
    return;
  }

  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}books/explore/${userId}`);
    results.value = await fetchBookDetails(res.data); 
  } catch (err: any) {
    error.value = "Không thể tải sách.";
  } finally {
    loading.value = false;
  }
}

async function applyFilters() {
  hasFiltered.value = true;
  loading.value = true;
  error.value = null;
  const userId = userInfo.value?.id || userInfo.value?.user_id;

  const payload = {
    genres_include: filters.value.genres_include.split(',').map(s => s.trim()).filter(Boolean),
    genres_exclude: filters.value.genres_exclude.split(',').map(s => s.trim()).filter(Boolean),
    page_min: filters.value.page_min,
    page_max: filters.value.page_max,
    year_min: filters.value.year_min,
    year_max: filters.value.year_max,
    user_id_to_exclude_books: filters.value.user_id_to_exclude_books ? userId : null,
  };

  try {
    const res = await axios.post(`${BOOK_SERVICE_URL}filter/books`, payload);
    results.value = await fetchBookDetails(res.data); 
    isOpen.value = false; 
  } catch (err: any) {
    error.value = "Lỗi khi lọc sách.";
  } finally {
    loading.value = false;
  }
}

function goToBook(bookId: number) {
  router.push(`/book/${bookId}`);
}

onMounted(loadInitialExplore);
</script>

<template>
  <Navbar />

  <div class="w-full max-w-5xl mx-auto m-5 space-y-6 px-4">
    <h1 class="text-2xl font-logo text-yellow-400 item-center">Khám phá</h1>

    <!-- (Bộ lọc giữ nguyên) -->
    <div class="bg-white border border-gray-200 rounded-lg shadow-sm ">
      <button @click="isOpen = !isOpen"
        class="focus:outline-none focus:ring-2 focus:ring-yellow-400 w-full flex items-center justify-start p-4 text-left focus:outline-none">
        <svg class="w-5 h-5 text-gray-600 transition-transform duration-300 ease-in-out"
          :class="{ 'rotate-90': isOpen }" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
          stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="m8.25 4.5 7.5 7.5-7.5 7.5" />
        </svg>
        <span class="ml-3 font-medium text-gray-800">Tùy chọn lọc</span>
      </button>

      <Transition enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100 translate-y-0"
        enter-active-class="transition ease-out duration-200" leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-2" leave-active-class="transition ease-in duration-150">
        <div v-show="isOpen" class="border-t border-gray-200 p-4">
          <!-- (Nội dung bộ lọc giữ nguyên) -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Thể loại (Bao gồm)</label>
              <input v-model="filters.genres_include" type="text"
                class="w-full border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-yellow-400 focus:outline-none" 
                placeholder="fantasy, sci-fi" />
              <p class="text-xs text-gray-400 mt-1">Cách nhau bằng dấu phẩy (,)</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Thể loại (Loại trừ)</label>
              <input v-model="filters.genres_exclude" type="text"
                class="w-full border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-yellow-400 focus:outline-none" 
                placeholder="romance" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Số trang (Tối thiểu)</label>
              <input v-model.number="filters.page_min" type="number"
                class="w-full border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-yellow-400 focus:outline-none" 
                placeholder="300" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Số trang (Tối đa)</label>
              <input v-model.number="filters.page_max" type="number"
                class="w-full border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-yellow-400 focus:outline-none" 
                placeholder="500" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Năm xuất bản (Từ)</label>
              <input v-model.number="filters.year_min" type="number"
                class="w-full border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-yellow-400 focus:outline-none" 
                placeholder="1990" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-600 mb-1">Năm xuất bản (Đến)</label>
              <input v-model.number="filters.year_max" type="number"
                class="w-full border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-yellow-400 focus:outline-none" 
                placeholder="2000" />
            </div>
          </div>
          <div class="mt-4">
            <label class="inline-flex items-center">
              <input type="checkbox" v-model="filters.user_id_to_exclude_books" 
                class="form-checkbox h-4 w-4 text-yellow-500 border-gray-300 rounded focus:ring-yellow-400">
              <span class="ml-2 text-gray-700">Loại bỏ sách đã có trên kệ</span>
            </label>
          </div>
          <div class="flex justify-end mt-4">
            <button
              @click="applyFilters"
              class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md"
            >
              Lọc kết quả
            </button>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Kết quả -->
    <div>
      <div v-if="loading" class="text-center text-gray-500 py-10">
        Đang tải sách...
      </div>
      <div v-else-if="error" class="text-center text-red-500 py-10">
        {{ error }}
      </div>
      
      <div v-else-if="results.length === 0" class="text-center text-gray-500 py-10">
        <p v-if="hasFiltered">
          Không tìm thấy cuốn sách nào khớp với bộ lọc của bạn.
        </p>
        <p v-else>
          Bạn đã xem hết sách "Khám phá" hoặc chưa có sách nào trong hệ thống.
        </p>
      </div>
      
      <div v-else class="space-y-6">
        <div 
          v-for="book in results" 
          :key="book.id"
          class="flex flex-col md:flex-row gap-5 bg-white p-4 rounded-lg border shadow-sm"
        >
          <!-- Bìa sách -->
          <img 
            v-if="book.cover_url"
            :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`"
            :alt="book.title"
            class="w-32 md:w-36 h-auto object-contain rounded shadow-md flex-shrink-0 cursor-pointer"
            @click="goToBook(book.id)"
          />
          <div v-else class="w-32 md:w-36 h-48 bg-gray-100 rounded flex items-center justify-center text-4xl text-gray-400 flex-shrink-0">
            📚
          </div>
          
          <!-- Thông tin sách (Giữa) -->
          <div class="flex-1">
            <h3 
              @click="goToBook(book.id)"
              class="text-xl font-bold text-gray-800 cursor-pointer hover:text-yellow-700"
            >
              {{ book.title }}
            </h3>
            <p class="text-md text-gray-600 mt-1">bởi {{ book.authorName }}</p>
            
            <p class="text-sm text-gray-500 mt-2">
              {{ book.page_count || 'N/A' }} trang
              <span v-if="book.published_date">
                &bull; Xuất bản {{ new Date(book.published_date).getFullYear() }}
              </span>
            </p>
            
            <div class="flex flex-wrap gap-2 mt-3">
              <span 
                v-for="genre in book.categories.slice(0, 5)" 
                :key="genre"
                class="px-2 py-0.5 bg-yellow-50 text-yellow-700 text-xs font-medium rounded-full border border-yellow-200"
              >
                {{ genre }}
              </span>
            </div>
          </div>
          
          <!-- Nút trạng thái (Phải) -->
          <div class="w-full md:w-40 flex-shrink-0">
            <BookStatusSelect 
              v-if="userInfo?.id || userInfo?.user_id"
              :book-id="book.id" 
              :user-id="userInfo?.id || userInfo?.user_id"
              :modelValue="book.statusObject"
              @update:modelValue="newStatus => book.statusObject = newStatus"
            />
            <div v-else>
              <p class="text-sm text-gray-500">Đăng nhập để thêm sách</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    
  </div>
</template>

