<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import Navbar from '../components/layout/Navbar.vue';
import { BOOK_SERVICE_URL, USER_SERVICE_URL, COVER_IMAGE_SERVER_URL, AVATAR_SERVER_URL } from '../config';

const route = useRoute();
const loading = ref(false);
const error = ref<string | null>(null);

const bookResults = ref<any[]>([]);
const userResults = ref<any[]>([]);

// Hàm này gọi cả 2 API cùng lúc
async function performSearch(query: string) {
  if (!query) return;

  loading.value = true;
  error.value = null;
  bookResults.value = [];
  userResults.value = [];

  try {
    // Gọi song song 2 API
    const [bookRes, userRes] = await Promise.all([
      // 1. API Tìm Sách (bạn đã có)
      axios.get(`${BOOK_SERVICE_URL}books/search`, { params: { q: query, limit: 10 } }),
      // 2. API Tìm Người dùng (bạn đã có)
      axios.get(`${USER_SERVICE_URL}users/search`, { params: { query: query } })
    ]);

    bookResults.value = bookRes.data || [];
    userResults.value = userRes.data || [];

  } catch (err) {
    console.error(err);
    error.value = "Đã xảy ra lỗi trong quá trình tìm kiếm.";
  } finally {
    loading.value = false;
  }
}

// 1. Tìm kiếm ngay khi trang được tải
onMounted(() => {
  const query = route.query.q as string;
  performSearch(query);
});

// 2. Tìm kiếm lại khi người dùng gõ tìm kiếm mới (trên Navbar)
watch(() => route.query.q, (newQuery) => {
  performSearch(newQuery as string);
});
</script>

<template>
  <Navbar />
  <div class="w-full max-w-5xl mx-auto m-5 space-y-8 px-4">
    <h1 class="text-2xl font-semibold text-gray-800">
      Kết quả tìm kiếm cho:
      <span class="text-yellow-500 font-bold">{{ route.query.q }}</span>
    </h1>

    <div v-if="loading" class="text-center text-gray-500 py-10">
      Đang tìm kiếm...
    </div>
    <div v-else-if="error" class="text-center text-red-500 py-10">
      {{ error }}
    </div>

    <!-- Nếu không có kết quả nào -->
    <div v-else-if="bookResults.length === 0 && userResults.length === 0" class="text-center text-gray-500 py-10">
      Không tìm thấy kết quả nào.
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-[2fr_1fr] gap-8">
      
      <!-- CỘT 1: KẾT QUẢ SÁCH -->
      <div class="space-y-6">
        <h2 class="text-xl font-bold text-gray-700 border-b pb-2">
          Sách ({{ bookResults.length }})
        </h2>
        <div v-if="bookResults.length === 0" class="text-gray-500 italic">
          Không tìm thấy sách nào.
        </div>
        
        <router-link 
          v-for="book in bookResults" 
          :key="book.id"
          :to="{ name: 'book', params: { id: book.id } }"
          class="flex gap-4 bg-white p-3 rounded-lg border shadow-sm hover:shadow-md transition"
        >
          <img 
            v-if="book.cover_url"
            :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`"
            :alt="book.title"
            class="w-16 h-24 object-cover rounded shadow-sm flex-shrink-0"
          />
          <div v-else class="w-16 h-24 bg-gray-100 rounded flex items-center justify-center text-3xl text-gray-400 flex-shrink-0">
            📚
          </div>
          <div>
            <h3 class="text-lg font-semibold text-gray-800 hover:text-yellow-700">{{ book.title }}</h3>
            <!-- (Lưu ý: API search-book của bạn chưa trả về Tác giả, nếu có thì sẽ tốt hơn) -->
            <p class="text-sm text-gray-500">{{ book.page_count || 0 }} trang</p>
          </div>
        </router-link>
      </div>

      <!-- CỘT 2: KẾT QUẢ NGƯỜI DÙNG -->
      <div class="space-y-6">
        <h2 class="text-xl font-bold text-gray-700 border-b pb-2">
          Người dùng ({{ userResults.length }})
        </h2>
        <div v-if="userResults.length === 0" class="text-gray-500 italic">
          Không tìm thấy người dùng nào.
        </div>
        
        <router-link 
          v-for="user in userResults" 
          :key="user.id"
          :to="{ name: 'profile', params: { id: user.id } }"
          class="flex items-center gap-3 p-3 bg-white border rounded-lg shadow-sm hover:shadow-md transition"
        >
          <div v-if="user.avatar_url" class="flex-shrink-0">
            <img 
              :src="`${AVATAR_SERVER_URL}/${user.avatar_url}`" 
              :alt="user.username"
              class="w-10 h-10 rounded-full bg-gray-200 object-cover"
            />
          </div>
          <div v-else class="flex-shrink-0">
            <div class="w-10 h-10 rounded-full bg-yellow-400 flex items-center justify-center">
              <span class="text-lg font-semibold text-white">
                {{ user.username?.charAt(0).toUpperCase() }}
              </span>
            </div>
          </div>
          <span class="font-semibold text-gray-800 hover:text-yellow-700">{{ user.username }}</span>
        </router-link>
      </div>

    </div>
  </div>
</template>