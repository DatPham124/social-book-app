<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import Navbar from "../layout/Navbar.vue";
import axios from "axios";
import { REVIEW_SERVICE_URL, AVATAR_SERVER_URL } from "../../config";
import { useAuth } from "../../composables/useAuth";
import { getProfile } from "../../composables/useProfile";
import { useBooks } from "../../composables/useBook";

const { userInfo } = useAuth();
const { fetchBook } = useBooks(); 

const userID_from_token = computed(() => userInfo.value?.user_id);

const route = useRoute();
const router = useRouter();

const bookId = Number(route.params.bookId);
const reviewId = Number(route.params.reviewId);

const book = ref<any>(null);
const profile = ref<any>(null);
const review = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);

async function getReviewDetail() {
  try {
    const response = await axios.get(`${REVIEW_SERVICE_URL}review/${reviewId}`);
    return response.data;
  } catch (e) {
    console.error("Lỗi khi tải đánh giá:", e);
    error.value = "Không thể tải đánh giá.";
    return null;
  }
}

function renderStars(rating: number) {
  const stars = [];
  const fullStars = Math.floor(rating);
  const hasHalf = rating % 1 >= 0.5;
  const emptyStars = 5 - fullStars - (hasHalf ? 1 : 0);

  for (let i = 0; i < fullStars; i++) stars.push("full");
  if (hasHalf) stars.push("half");
  for (let i = 0; i < emptyStars; i++) stars.push("empty");
  return stars;
}

function editReview() {
  router.push({ name: "ReviewBook", params: { id: bookId } });
}

onMounted(async () => {
  loading.value = true;

  profile.value = await getProfile(userInfo.value?.user_id);

  review.value = await getReviewDetail();

  book.value = await fetchBook(bookId, userInfo.value?.user_id);

  console.log("📚 Chi tiết sách:", book.value);
  console.log("✍️ Review:", review.value);

  loading.value = false;
});
</script>

<template>
  <Navbar />
  <div class="max-w-3xl mx-auto px-6 py-10">
    <div v-if="loading" class="text-center text-gray-500 py-12">Đang tải dữ liệu...</div>
    <div v-else-if="error" class="text-center text-red-500 py-12">{{ error }}</div>

    <div v-else>
      <div class="flex items-center gap-4 mb-4">
        <div
          class="w-14 h-14 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm"
        >
          <template v-if="profile?.avatar_url">
            <img
              :src="`${AVATAR_SERVER_URL}/${profile.avatar_url}`"
              alt="Ảnh đại diện người dùng"
              class="w-full h-full object-cover"
            />
          </template>
          <template v-else>
            {{ profile?.username?.charAt(0)?.toUpperCase() || "U" }}
          </template>
        </div>

        <div>
          <p class="text-sm text-teal-600 font-semibold">Bài đánh giá của bạn cho:</p>
          <h2 class="text-xl font-bold text-gray-900">
            {{ book?.title || "Chưa có tên sách" }}
            <span class="text-gray-700"> - {{ book?.author || "Không rõ tác giả" }}</span>
          </h2>
        </div>
      </div>

      <div class="flex items-center gap-2 mt-2">
        <template v-for="(type, i) in renderStars(review?.rating || 0)" :key="i">
          <font-awesome-icon v-if="type === 'full'" icon="fa-solid fa-star" class="text-yellow-400 text-xl" />
          <font-awesome-icon v-else-if="type === 'half'" icon="fa-solid fa-star-half-alt" class="text-yellow-400 text-xl" />
          <font-awesome-icon v-else icon="fa-regular fa-star" class="text-yellow-400 text-xl" />
        </template>
        <span class="text-gray-800 font-medium text-lg">{{ (review?.rating || 0).toFixed(1) }}</span>
      </div>

      <hr class="my-4" />

      <p class="text-gray-700 text-base leading-relaxed">
        {{ review?.content || "Bạn chưa để lại bình luận nào." }}
      </p>

      <button
        @click="editReview"
        class="mt-6 px-5 py-2 bg-teal-600 text-white rounded-md hover:bg-teal-700 transition"
      >
        Chỉnh sửa đánh giá
      </button>
    </div>
  </div>
</template>

<style scoped>
</style>
