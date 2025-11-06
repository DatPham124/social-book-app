<script setup lang="ts">
import Navbar from '../components/layout/Navbar.vue';
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL, AVATAR_SERVER_URL } from '../config';
import { useAuth } from '../composables/useAuth';
import { getProfile } from '../composables/useProfile';
import { useBooks } from '../composables/useBook';
import BookStatusSelect from '../components/books/BookStatusSelect.vue'; 

interface Category {
  id: number;
  name: string;
}

const { userInfo } = useAuth();
const router = useRouter();
const { getUserBookStatus } = useBooks();

const isOpen = ref(true);
const loading = ref(true);
const results = ref<any[]>([]);
const error = ref<string | null>(null);
const hasFiltered = ref(false);
const allCategories = ref<Category[]>([]); 

const filters = ref({
  genres_include: [] as string[],
  genres_exclude: [] as string[],
  page_filter: null as string | null,
  year_min: null as number | null,
  year_max: null as number | null,
  book_type: null as string | null,
  user_id_to_exclude_books: true,
});

const statusMap = {
  add_book: "Thêm vào kệ",
  to_read: "Sẽ đọc",
  currently_reading: "Đang đọc",
  read: "Đã đọc",
  dnf: "Chưa hoàn thành",
};

async function loadCategories() {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}category/`);
    allCategories.value = res.data;
  } catch (err) {
    console.error("Không thể tải danh sách thể loại");
  }
}

async function fetchBookDetails(books: any[]) {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  
  const booksWithDetails = await Promise.all(
    books.map(async (book: any) => {
      const [profile, statusResult] = await Promise.all([
        getProfile(book.authorID), 
        userId ? getUserBookStatus(userId, book.id) : null 
      ]);
      
      const statusKey = statusResult?.status || 'add_book';
      const statusObject = {
        value: statusKey,
        label: statusMap[statusKey as keyof typeof statusMap] || "Thêm vào kệ"
      };
      
      return { 
        ...book, 
        authorName: profile?.username || "Không rõ tác giả",
        statusObject: statusObject,
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

  let page_min: number | null = null;
  let page_max: number | null = null;

  if (filters.value.page_filter === 'lt300') {
    page_min = 0;
    page_max = 299;
  } else if (filters.value.page_filter === '300-499') {
    page_min = 300;
    page_max = 499;
  } else if (filters.value.page_filter === 'gt500') {
    page_min = 500;
    page_max = null;
  }

  const payload = {
    genres_include: filters.value.genres_include,
    genres_exclude: filters.value.genres_exclude,
    page_min: page_min,
    page_max: page_max,
    year_min: filters.value.year_min,
    year_max: filters.value.year_max,
    book_type: filters.value.book_type,
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

onMounted(() => {
  loadInitialExplore();
  loadCategories();
});
</script>

<template>
  <Navbar />

  <div class="w-full max-w-5xl mx-auto m-5 space-y-6 px-4">
    <h1 class="text-2xl font-logo text-yellow-400 item-center">Khám phá</h1>

    <div class="bg-white border border-gray-200 rounded-lg shadow-sm ">
      <button @click="isOpen = !isOpen"
        class="focus:outline-none focus:ring-2 focus:ring-yellow-400 w-full flex items-center justify-start p-4 text-left focus:outline-none">
        <svg class="w-5 h-5 text-gray-600 transition-transform duration-300 ease-in-out"
          :class="{ 'rotate-0': isOpen, '-rotate-90': !isOpen }" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
          stroke-width="2" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="m19.5 8.25-7.5 7.5-7.5-7.5" />
        </svg>
        <span class="ml-3 font-medium text-gray-800">Lọc tất cả sách</span>
      </button>

      <div v-show="isOpen" class="border-t border-gray-200 p-4 space-y-6">
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Type (MỚI - Đơn giản)</label>
          <div class="flex gap-4">
            <label class="flex items-center text-sm">
              <input type="radio" value="Fiction" v-model="filters.book_type" class="form-radio h-4 w-4 text-yellow-500 focus:ring-yellow-400">
              <span class="ml-2 text-gray-700">Hư cấu (Fiction)</span>
            </label>
            <label class="flex items-center text-sm">
              <input type="radio" value="Nonfiction" v-model="filters.book_type" class="form-radio h-4 w-4 text-yellow-500 focus:ring-yellow-400">
              <span class="ml-2 text-gray-700">Phi hư cấu (Nonfiction)</span>
            </label>
            <label class="flex items-center text-sm">
              <input type="radio" :value="null" v-model="filters.book_type" class="form-radio h-4 w-4 text-yellow-500 focus:ring-yellow-400">
              <span class="ml-2 text-gray-700">Tất cả</span>
            </label>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Thể loại</label>
          <div class="max-h-40 overflow-y-auto border rounded-md p-2 grid grid-cols-2 md:grid-cols-3 gap-2">
            <label 
              v-for="category in allCategories" 
              :key="category.id" 
              class="flex items-center text-sm cursor-pointer"
            >
              <input 
                type="checkbox"
                :value="category.name"
                v-model="filters.genres_include"
                class="form-checkbox h-4 w-4 text-yellow-500 rounded focus:ring-yellow-400"
              />
              <span class="ml-2 text-gray-700">{{ category.name }}</span>
            </label>
          </div>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Số trang</label>
          <div class="flex flex-wrap gap-4">
            <label class="flex items-center text-sm">
              <input type="radio" value="lt300" v-model="filters.page_filter" class="form-radio h-4 w-4 text-yellow-500 focus:ring-yellow-400">
              <span class="ml-2 text-gray-700">&lt; 300</span>
            </label>
            <label class="flex items-center text-sm">
              <input type="radio" value="300-499" v-model="filters.page_filter" class="form-radio h-4 w-4 text-yellow-500 focus:ring-yellow-400">
              <span class="ml-2 text-gray-700">300-499</span>
            </label>
            <label class="flex items-center text-sm">
              <input type="radio" value="gt500" v-model="filters.page_filter" class="form-radio h-4 w-4 text-yellow-500 focus:ring-yellow-400">
              <span class="ml-2 text-gray-700">500+</span>
            </label>
            <label class="flex items-center text-sm">
              <input type="radio" :value="null" v-model="filters.page_filter" class="form-radio h-4 w-4 text-yellow-500 focus:ring-yellow-400">
              <span class="ml-2 text-gray-700">Tất cả</span>
            </label>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Năm xuất bản</label>
          <div class="flex items-center gap-3">
            <input vd-model.number="filters.year_min" type="number"
              class="w-full md:w-32 border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-yellow-400 focus:outline-none" 
              placeholder="Từ (VD: 1990)" />
            <span class="text-gray-500">-</span>
            <input v-model.number="filters.year_max" type="number"
              class="w-full md:w-32 border rounded-md px-3 py-2 text-sm focus:ring-2 focus:ring-yellow-400 focus:outline-none" 
              placeholder="Đến (VD: 2000)" />
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Chỉ hiển thị sách</label>
          <div class="space-y-1">
            <label class="flex items-center text-sm">
              <input type="checkbox" v-model="filters.user_id_to_exclude_books" 
                class="form-checkbox h-4 w-4 text-yellow-500 border-gray-300 rounded focus:ring-yellow-400">
              <span class="ml-2 text-gray-700">Chưa có trên kệ của tôi</span>
            </label>
          </div>
        </div>

        <div class="flex justify-end mt-4">
          <button
            @click="applyFilters"
            class="px-5 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md"
          >
            Lọc
          </button>
        </div>
      </div>
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