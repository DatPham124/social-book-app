<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';
import { REVIEW_SERVICE_URL, COVER_IMAGE_SERVER_URL } from '../../config';
import { useBooks } from '../../composables/useBook';
import { getProfile } from '../../composables/useProfile';
import Navbar from '../layout/Navbar.vue';

const route = useRoute();
const { getBookById } = useBooks();

const userID = Number(route.params.id);
const profile = ref<any>(null);
const reviews = ref<any[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

async function loadAllReviews() {
  if (!userID) {
    error.value = "Không tìm thấy ID người dùng";
    loading.value = false;
    return;
  }

  try {
    // 1. Lấy profile (để lấy tên)
    profile.value = await getProfile(userID);
    
    // 2. Lấy danh sách review (API mới ở Bước 1)
    const res = await axios.get(`${REVIEW_SERVICE_URL}review/user/${userID}`);
    const reviewList = res.data;

    // 3. Gộp thông tin sách cho từng review
    const reviewsWithBook = await Promise.all(
      reviewList.map(async (review: any) => {
        const book = await getBookById(review.book_id);
        return { ...review, book: book || null };
      })
    );
    reviews.value = reviewsWithBook.filter(r => r.book); // Chỉ giữ review có sách

  } catch (err: any) {
    if (err.response?.status === 404) {
      error.value = "Người dùng này chưa có đánh giá nào.";
    } else {
      error.value = "Lỗi khi tải đánh giá.";
    }
    console.error(err);
  } finally {
    loading.value = false;
  }
}

onMounted(loadAllReviews);
</script>

<template>
  <Navbar />
  <div class="w-full max-w-3xl mx-auto p-4 md:p-6">
    <div v-if="loading" class="text-center text-gray-500 py-10">
      Đang tải đánh giá...
    </div>
    <div v-else-if="error" class="text-center text-gray-500 py-10 italic">
      {{ error }}
    </div>
    
    <div v-else>
      <h1 class="text-2xl font-bold text-gray-800 mb-6">
        Tất cả đánh giá của {{ profile?.username }}
      </h1>
      
      <!-- Danh sách đánh giá -->
      <div class="space-y-6">
        <div 
          v-for="review in reviews" 
          :key="review.id"
          class="flex gap-4 bg-white p-4 rounded-lg border shadow-sm"
        >
          <!-- Bìa sách -->
          <router-link :to="{ name: 'book', params: { id: review.book.id } }">
            <img 
              v-if="review.book.cover_url"
              :src="`${COVER_IMAGE_SERVER_URL}/${review.book.cover_url}`"
              :alt="review.book.title"
              class="w-20 h-28 object-cover rounded shadow-sm flex-shrink-0"
            />
            <div v-else class="w-20 h-28 bg-gray-100 rounded flex items-center justify-center text-3xl">📚</div>
          </router-link>
          
          <!-- Nội dung Review -->
          <div class="flex-1">
            <router-link :to="{ name: 'book', params: { id: review.book.id } }">
              <h3 class="text-lg font-semibold text-gray-800 hover:text-yellow-600">
                {{ review.book.title }}
              </h3>
            </router-link>
            
            <!-- Sao -->
            <p class="text-lg font-medium text-yellow-500 mt-1">
              <span v-for="i in Math.floor(review.rating)" :key="i">⭐️</span>
            </p>
            
            <!-- Nội dung -->
            <p v-if="review.content" class="text-gray-700 mt-2 italic whitespace-pre-line">
              "{{ review.content }}"
            </p>
            
            <p class="text-xs text-gray-400 mt-2">
              Đánh giá ngày: {{ new Date(review.created_at).toLocaleDateString('vi-VN') }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>