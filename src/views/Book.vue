<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import Navbar from "../components/layout/Navbar.vue";
import { useBooks } from "../composables/useBook";
import { COVER_IMAGE_SERVER_URL } from "../config";
import { jwtDecode } from "jwt-decode";
import BookProgress from "../components/books/BookProgress.vue";
import BookStatusSelect from "../components/books/BookStatusSelect.vue";

const { fetchBook, formatDate } = useBooks();
const route = useRoute();

const book = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const bookId = Number(route.params.id);
const currentStatus = ref<{ value: string; label: string } | null>(null);
const userInfo = ref<any>(null);

const statuses = [
  { value: "to_read", label: "Sẽ đọc" },
  { value: "currently_reading", label: "Đang đọc" },
  { value: "read", label: "Đã đọc" },
  { value: "dnf", label: "Chưa hoàn thành" },
];

function mapStatus(value: string) {
  return statuses.find((s) => s.value === value) || statuses[0];
}

const token = localStorage.getItem("token");
if (token) {
  try {
    const decoded = jwtDecode<any>(token);
    if (decoded.exp * 1000 > Date.now()) userInfo.value = decoded;
    else localStorage.removeItem("token");
  } catch {
    localStorage.removeItem("token");
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

onMounted(async () => {
  try {
    loading.value = true;
    if (!bookId) {
      error.value = "Không tìm thấy ID sách.";
      return;
    }
    const data = await fetchBook(bookId, userInfo.value?.user_id);
    if (!data) {
      error.value = "Không tìm thấy dữ liệu sách.";
      return;
    }
    book.value = data;
    currentStatus.value = mapStatus(data.status || "to_read");
  } catch (err) {
    console.error(err);
    error.value = "Đã xảy ra lỗi khi tải dữ liệu sách.";
  } finally {
    loading.value = false;
  }
});

function formatYear(dateString: string) {
  if (!dateString) return "—";
  return new Date(dateString).getFullYear();
}
</script>

<template>
  <Navbar />

  <div class="max-w-7xl mx-auto px-6 py-10">
    <div v-if="loading" class="text-center text-gray-500 py-12">Đang tải dữ liệu sách...</div>
    <div v-else-if="error" class="text-center text-red-500 py-12">{{ error }}</div>

    <div v-else class="grid grid-cols-12 gap-8">
      <div class="col-span-3 space-y-6">
        <div class="rounded-lg overflow-hidden shadow-md bg-gray-50">
          <img :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" :alt="book.title"
            class="w-full h-auto object-cover" />
        </div>

        <div class="bg-white border rounded-lg shadow-sm p-4">
          <h3 class="font-semibold mb-2 text-gray-800 text-sm uppercase tracking-wide">Hoạt động bạn bè</h3>
          <p class="text-gray-500 text-sm italic">Chưa có ai bạn theo dõi tương tác với sách này.</p>
        </div>
      </div>

      <div class="col-span-6 space-y-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">{{ book.title }}</h1>
          <p class="text-gray-700 text-sm mt-1">{{ book.author }}</p>
          <p class="text-gray-500 text-sm mt-2">
            {{ book.page_count }} trang • {{ book.language }} • {{ formatYear(book.published_date) }}
          </p>
        </div>

        <div class="flex flex-wrap gap-2">
          <span v-for="category in book.categories" :key="category"
            class="px-3 py-1 text-xs rounded-full bg-yellow-100 text-yellow-700 font-medium">
            {{ category }}
          </span>
        </div>

        <div class="bg-white border rounded-lg shadow-sm p-4">
          <h3 class="font-semibold text-gray-800 mb-2 uppercase text-sm tracking-wide">Giới thiệu nội dung</h3>
          <p class="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
            {{ book.description || "Chưa có mô tả cho cuốn sách này." }}
          </p>
        </div>

        <div class="bg-white border rounded-lg shadow-sm p-4">
          <h3 class="font-semibold text-gray-800 mb-2 uppercase text-sm tracking-wide">Đánh giá từ cộng đồng</h3>
          <div class="flex items-center space-x-2">
            <span class="text-2xl font-bold text-teal-600">{{ (book.rating || 0).toFixed(1) }}</span>
            <div class="flex items-center text-yellow-400">
              <template v-for="(type, i) in renderStars(book.rating || 0)" :key="i">
                <font-awesome-icon v-if="type === 'full'" icon="fa-solid fa-star" class="w-5 h-5" />
                <font-awesome-icon v-else-if="type === 'half'" icon="fa-solid fa-star-half-alt" class="w-5 h-5" />
                <font-awesome-icon v-else icon="fa-regular fa-star" class="w-5 h-5" />
              </template>
            </div>
            <span class="text-gray-500 text-sm">dựa trên {{ book.review_count || 0 }}

              <RouterLink :to="{ name: 'ListReview', params: { id: bookId } }"
                class="text-yellow-600 hover:text-yellow-700 font-semibold">
                lượt đánh giá
              </RouterLink>


            </span>
          </div>
        </div>

        <div class="bg-white border rounded-lg shadow-sm p-4">
          <h3 class="font-semibold text-gray-800 mb-2 uppercase text-sm tracking-wide">Cảnh báo nội dung</h3>
          <template v-if="book.warnings.length">
            <ul class="list-disc list-inside space-y-1 text-gray-700 text-sm">
              <li v-for="warn in book.warnings" :key="warn">{{ warn }}</li>
            </ul>
          </template>
          <p v-else class="text-gray-600 text-sm italic">Chưa có cảnh báo nội dung nào được thêm.</p>
        </div>
      </div>

      <div class="col-span-3 space-y-6">
        <RouterLink :to="{ name: 'ReviewBook', params: { id: bookId }, query: { user: userInfo?.user_id } }"
          class="block text-yellow-600 hover:text-yellow-700 font-semibold">
          ✍️ Viết đánh giá cho sách
        </RouterLink>

        <div class="bg-white border rounded-lg shadow-sm p-4 space-y-3">
          <BookProgress :book="book" :userId="userInfo?.user_id || 1" @update="(updatedBook) => (book = updatedBook)" />
          <BookStatusSelect v-if="currentStatus" v-model="currentStatus" :bookId="book.id"
            :userId="userInfo?.user_id || 1" />

          <button class="w-full py-1.5 rounded border text-sm text-gray-700 hover:bg-gray-50">
            💛 Thêm vào danh sách yêu thích
          </button>
          <button class="w-full py-1.5 rounded border text-sm text-gray-700 hover:bg-gray-50">
            📚 Đánh dấu là đã sở hữu
          </button>
        </div>

        <div class="text-sm text-gray-700 space-y-2">
          <a href="#" class="block text-yellow-600 hover:text-yellow-700">Khám phá các sách tương tự...</a>
          <a href="#" class="block text-yellow-600 hover:text-yellow-700">Bắt đầu đọc cùng bạn bè...</a>
          <a href="#" class="block text-yellow-600 hover:text-yellow-700">Tạo thử thách đọc mới...</a>
          <a href="#" class="block text-yellow-600 hover:text-yellow-700">Xem ngân hàng câu hỏi...</a>
        </div>

        <div class="border-t border-gray-200 pt-4 text-sm text-gray-600">
          <p><strong>Ngày phát hành:</strong> {{ formatDate(book.published_date) }}</p>
          <p><strong>Tổng số trang:</strong> {{ book.page_count }}</p>
          <p><strong>Ngôn ngữ:</strong> {{ book.language }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
