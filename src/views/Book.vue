<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute } from "vue-router";
import Navbar from "../components/layout/Navbar.vue";
// 1. IMPORT CÁC HÀM CẦN THIẾT
import { useBooks } from "../composables/useBook";
import { getProfile } from "../composables/useProfile";
import { BOOK_SERVICE_URL, USER_SERVICE_URL, AVATAR_SERVER_URL, COVER_IMAGE_SERVER_URL } from "../config";
import { jwtDecode } from "jwt-decode";
import axios from "axios";
import BookProgress from "../components/books/BookProgress.vue";
import BookStatusSelect from "../components/books/BookStatusSelect.vue";

// IMPORT HÀM updateReadingDates
const { fetchBook, formatDate, toggleFavoriteStatus, getUserBookStatus, updateReadingDates } = useBooks();
const route = useRoute();

const book = ref<any>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const bookId = Number(route.params.id);
const currentStatus = ref<{ value: string; label: string } | null>(null);
const userInfo = ref<any>(null);

const friendActivity = ref<any[]>([]);
const loadingFriends = ref(true);
const friendError = ref<string | null>(null);

// STATE MỚI CHO VIỆC SỬA NGÀY
const isEditingDates = ref(false);
const isSavingDates = ref(false);
const tempStartDate = ref<string | null>(null);
const tempFinishDate = ref<string | null>(null);

// STATE MỚI CHO AI SUMMARY
const showAiSummaryModal = ref(false);
const isLoadingAiSummary = ref(false);
const aiSummaryText = ref("");

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

async function loadFriendActivity() {
  loadingFriends.value = true;
  friendError.value = null;

  if (!userInfo.value || !token) {
    loadingFriends.value = false;
    return;
  }

  const currentUserId = userInfo.value.user_id;

  try {
    const friendListRes = await axios.get(
      `${USER_SERVICE_URL}friends/${currentUserId}/accepted`,
      { headers: { Authorization: `Bearer ${token}` } }
    );

    if (!friendListRes.data || friendListRes.data.length === 0) {
      friendActivity.value = [];
      loadingFriends.value = false;
      return;
    }

    const activities = await Promise.all(
      friendListRes.data.map(async (friendship: any) => {
        const friendId = friendship.user_id === currentUserId
          ? friendship.friend_id
          : friendship.user_id;

        const [profile, status] = await Promise.all([
          getProfile(friendId),
          getUserBookStatus(friendId, bookId)
        ]);

        if (profile && status) {
          return {
            id: friendId,
            username: profile?.username || 'Bạn bè',
            avatar: profile?.avatar_url,
            status: status.status,
          };
        }
        return null;
      })
    );

    friendActivity.value = activities.filter(a => a !== null);

  } catch (err: any) {
    console.error("Lỗi khi tải hoạt động bạn bè:", err);
    if (err.response?.status === 404) {
      friendError.value = "Bạn chưa có bạn bè nào.";
    } else {
      friendError.value = "Không thể tải hoạt động bạn bè.";
    }
  } finally {
    loadingFriends.value = false;
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

  loadFriendActivity();
});

function formatYear(dateString: string) {
  if (!dateString) return "—";
  return new Date(dateString).getFullYear();
}

const isTogglingFavorite = ref(false);

async function handleToggleFavorite() {
  if (!book.value || !userInfo.value || isTogglingFavorite.value) return;

  isTogglingFavorite.value = true;
  const currentUserId = userInfo.value.user_id;
  const currentBookId = book.value.id;
  const currentFavState = book.value.is_favorite;

  const newState = await toggleFavoriteStatus(currentUserId, currentBookId, currentFavState);

  book.value.is_favorite = newState;
  isTogglingFavorite.value = false;
}

function getFriendStatusText(status: string) {
  switch (status) {
    case 'read': return 'đã đọc';
    case 'currently_reading': return 'đang đọc';
    case 'to_read': return 'thêm vào kệ "Sẽ đọc"';
    case 'dnf': return 'đã bỏ dở';
    default: return 'đã tương tác với';
  }
}

function formatDateForInput(dateString: string | null) {
  if (!dateString) return '';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    return date.toISOString().split('T')[0];
  } catch (e) {
    return '';
  }
}

function openDateEditor() {
  tempStartDate.value = formatDateForInput(book.value.start_date);
  tempFinishDate.value = formatDateForInput(book.value.finish_date);
  isEditingDates.value = true;
}

async function saveDates() {
  if (!userInfo.value) return;
  isSavingDates.value = true;
  
  try {
    const userId = userInfo.value.user_id;
    const bookId = book.value.id;

    const newStartDate = tempStartDate.value || null;
    const newFinishDate = tempFinishDate.value || null;

    const updatedStatus = await updateReadingDates(userId, bookId, newStartDate, newFinishDate);
    
    book.value.start_date = updatedStatus.start_date;
    book.value.finish_date = updatedStatus.finish_date;
    
    isEditingDates.value = false;
  } catch (error) {
    console.error("Lỗi khi lưu ngày:", error);
    alert("Không thể lưu ngày. Vui lòng thử lại.");
  } finally {
    isSavingDates.value = false;
  }
}

// *** HÀM MỚI (ĐÃ SỬA) ĐỂ GỌI API TEST CỦA BẠN ***
async function getAISummary() {
  if (!book.value) return;
  isLoadingAiSummary.value = true;
  aiSummaryText.value = "";
  showAiSummaryModal.value = true;

  try {
    // 1. Chuẩn bị params
    const params = {
      book_title: book.value.title,
      book_author: book.value.author,       // (Trường 'author' này đã được 'fetchBook' lấy về)
      book_description: book.value.description // (Trường 'description' cũng đã được lấy về)
    };

    // 2. Gọi API test mới (books/ai-summary/)
    // API này không cần book_id trong path, mà nhận params
    const res = await axios.get(`${BOOK_SERVICE_URL}books/ai-summary/`, { params });
    
    aiSummaryText.value = res.data.summary_text;
  } catch (err: any) {
    aiSummaryText.value = "Lỗi: " + (err.response?.data?.detail || "Không thể tạo tóm tắt.");
  } finally {
    isLoadingAiSummary.value = false;
  }
}

</script>

<template>
  <Navbar />

  <div class="max-w-7xl mx-auto px-6 py-10">
    <div v-if="loading" class="text-center text-gray-500 py-12">Đang tải dữ liệu sách...</div>
    <div v-else-if="error" class="text-center text-red-500 py-12">{{ error }}</div>

    <div v-else class="grid grid-cols-12 gap-8">
      <!-- Cột 1 (Bìa sách) -->
      <div class="col-span-3 space-y-6">
        <div class="rounded-lg overflow-hidden shadow-md bg-gray-50">
          <img :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" :alt="book.title"
            class="w-full h-auto object-cover" />
        </div>

        <!-- Khối Hoạt động bạn bè -->
        <div class="bg-white border rounded-lg shadow-sm p-4">
          <h3 class="font-semibold mb-3 text-gray-800 text-sm uppercase tracking-wide">Hoạt động bạn bè</h3>
          <div v-if="loadingFriends" class="text-gray-500 text-sm italic">
            Đang tải...
          </div>
          <div v-else-if="friendError" class="text-gray-500 text-sm italic">
            {{ friendError }}
          </div>
          <div v-else-if="friendActivity.length === 0" class="text-gray-500 text-sm italic">
            Chưa có ai bạn theo dõi tương tác với sách này.
          </div>
          <div v-else class="space-y-3">
            <div v-for="friend in friendActivity" :key="friend.id" class="flex items-center space-x-2">
              <div v-if="friend.avatar" class="flex-shrink-0">
                <img :src="`${AVATAR_SERVER_URL}/${friend.avatar}`" :alt="friend.username"
                  class="w-8 h-8 rounded-full bg-gray-200 object-cover" />
              </div>
              <div v-else class="flex-shrink-0">
                <div class="w-8 h-8 rounded-full bg-yellow-400 flex items-center justify-center">
                  <span class="text-sm font-semibold text-white">
                    {{ friend.username?.charAt(0).toUpperCase() }}
                  </span>
                </div>
              </div>
              <div>
                <p class="text-sm font-medium text-gray-700">
                  {{ friend.username }}
                </p>
                <p class="text-xs text-yellow-600">
                  {{ getFriendStatusText(friend.status) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Cột 2 (Thông tin sách) -->
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

        <!-- KHỐI GIỚI THIỆU VÀ NÚT TÓM TẮT AI -->
        <div class="bg-white border rounded-lg shadow-sm p-4">
          <h3 class="font-semibold text-gray-800 mb-2 uppercase text-sm tracking-wide">Giới thiệu nội dung</h3>
          <p class="text-gray-700 text-sm leading-relaxed whitespace-pre-line">
            {{ book.description || "Chưa có mô tả cho cuốn sách này." }}
          </p>
          
          <!-- NÚT TÓM TẮT AI MỚI -->
          <button
            @click="getAISummary"
            class="mt-4 px-3 py-1.5 bg-gray-900 text-white text-xs font-semibold rounded-md shadow hover:bg-gray-700 transition-colors"
          >
            🤖 Xem tóm tắt bằng AI...
          </button>
        </div>

        <div class="bg-white border rounded-lg shadow-sm p-4">
          <h3 class="font-semibold text-gray-800 mb-2 uppercase text-sm tracking-wide">Đánh giá từ cộng đồng</h3>
          <div class="flex items-center space-x-2">
            <span class="text-2xl font-bold text-teal-600">{{ (book.rating).toFixed(1) }}</span>
            <div class="flex items-center text-yellow-400">
              <template v-for="(type, i) in renderStars(book.rating)" :key="i">
                <font-awesome-icon v-if="type === 'full'" icon="fa-solid fa-star" class="w-5 h-5" />
                <font-awesome-icon v-else-if="type === 'half'" icon="fa-solid fa-star-half-alt" class="w-5 h-5" />
                <font-awesome-icon v-else icon="fa-regular fa-star" class="w-5 h-5" />
              </template>
            </div>
            <span class="text-gray-500 text-sm">dựa trên {{ book.review_count }}
              <RouterLink :to="{ name: 'ListReview', params: { id: bookId } }"
                class="text-yellow-600 hover:text-yellow-700 font-semibold">
                lượt đánh giá
              </RouterLink>
            </span>
          </div>
        </div>

        <!-- KHỐI HOẠT ĐỘNG CỦA BẠN (ĐÃ THAY THẾ "CẢNH BÁO NỘI DUNG") -->
        <div class="bg-white border rounded-lg shadow-sm p-4" v-if="userInfo">
          <div class="flex justify-between items-center mb-2">
            <h3 class="font-semibold text-gray-800 uppercase text-sm tracking-wide">Hoạt động của bạn</h3>
            <button
              v-if="!isEditingDates"
              @click="openDateEditor"
              class="text-xs text-yellow-600 hover:text-yellow-700 font-semibold"
            >
              Chỉnh sửa ngày
            </button>
            <button
              v-else
              @click="isEditingDates = false"
              class="text-xs text-gray-500 hover:text-gray-700 font-semibold"
            >
              Hủy
            </button>
          </div>

          <div v-if="!isEditingDates" class="text-sm text-gray-700 space-y-1">
            <p v-if="book.status === 'read'">
              Bạn đã đọc xong sách
              <span v-if="book.start_date && book.finish_date">
                từ {{ formatDate(book.start_date) }} đến {{ formatDate(book.finish_date) }}.
              </span>
              <span v-else-if="book.finish_date">
                vào {{ formatDate(book.finish_date) }}.
              </span>
            </p>
            <p v-else-if="book.status === 'currently_reading'">
              Bạn bắt đầu đọc
              <span v-if="book.start_date">
                vào {{ formatDate(book.start_date) }}.
              </span>
              <span v-else>
                (chưa thêm ngày bắt đầu).
              </span>
            </p>
            <p v-else-if="book.status === 'to_read'">
              Sách đang ở kệ "Sẽ đọc".
            </p>
            <p v-else-if="book.status === 'dnf'">
              Bạn đã bỏ dở sách.
            </p>
          </div>

          <div v-else class="space-y-3">
            <div class="text-sm">
              <label class="block font-medium text-gray-700">Ngày bắt đầu</label>
              <input 
                type="date" 
                v-model="tempStartDate"
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-1.5 text-sm"
              />
            </div>
            <div class="text-sm">
              <label class="block font-medium text-gray-700">Ngày kết thúc</label>
              <input 
                type="date" 
                v-model="tempFinishDate"
                class="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-1.5 text-sm"
              />
            </div>
            <button
              @click="saveDates"
              :disabled="isSavingDates"
              class="w-full py-1.5 rounded text-sm transition-colors duration-200 bg-yellow-400 text-black font-semibold hover:bg-yellow-500"
            >
              <span v-if="isSavingDates">Đang lưu...</span>
              <span v-else>Lưu ngày</span>
            </button>
          </div>
        </div>
        
      </div>

      <!-- Cột 3 (Hành động) -->
      <div class="col-span-3 space-y-6">
        <RouterLink :to="{ name: 'ReviewBook', params: { id: bookId }, query: { user: userInfo?.user_id } }"
          class="block text-yellow-600 hover:text-yellow-700 font-semibold">
          ✍️ Viết đánh giá cho sách
        </RouterLink>

        <div class="bg-white border rounded-lg shadow-sm p-4 space-y-3">
          <BookProgress v-if="userInfo" :book="book" :userId="userInfo.user_id"
            @update="(updatedBook) => (book = updatedBook)" />
          <BookStatusSelect v-if="currentStatus && userInfo" v-model="currentStatus" :bookId="book.id"
            :userId="userInfo.user_id" />

          <button v-if="userInfo" @click="handleToggleFavorite" :disabled="isTogglingFavorite"
            class="w-full py-1.5 rounded border text-sm transition-colors duration-200" :class="[
              book.is_favorite
                ? 'bg-yellow-100 text-yellow-700 border-yellow-200 hover:bg-yellow-200'
                : 'text-gray-700 hover:bg-gray-50'
            ]">
            <span v-if="isTogglingFavorite">Đang lưu...</span>
            <span v-else>
              {{ book.is_favorite ? '💛 Đã yêu thích' : '💛 Thêm vào danh sách yêu thích' }}
            </span>
          </button>
        </div>

        <div class="text-sm text-gray-700 space-y-2">
          <a href="#" class="block text-yellow-600 hover:text-yellow-700">Khám phá các sách tương tự...</a>
          <a href="#" class="block text-yellow-600 hover:text-yellow-700">Bắt đầu đọc cùng bạn bè...</a>
          <a href="#" class="block text-yellow-600 hover:text-yellow-700">Tạo thử thách đọc mới...</a>
        </div>

        <div class="border-t border-gray-200 pt-4 text-sm text-gray-600">
          <p><strong>Ngày phát hành:</strong> {{ formatDate(book.published_date) }}</p>
          <p><strong>Tổng số trang:</strong> {{ book.page_count }}</p>
          <p><strong>Ngôn ngữ:</strong> {{ book.language }}</p>
        </div>
      </div>
    </div>
  </div>
  
  <!-- MODAL MỚI CHO AI SUMMARY -->
  <div
    v-if="showAiSummaryModal"
    @click.self="showAiSummaryModal = false"
    class="fixed inset-0 bg-opacity-30 backdrop-blur-sm flex justify-center items-center z-50 p-4"
  >
    <div class="bg-white rounded-lg shadow-xl w-full max-w-lg p-6">
      <div class="flex justify-between items-center mb-4">
        <h3 class="text-lg font-semibold text-gray-800">Tóm tắt bằng AI</h3>
        <button @click="showAiSummaryModal = false" class="text-gray-400 hover:text-gray-600">&times;</button>
      </div>
      
      <div v-if="isLoadingAiSummary" class="text-center text-gray-500 py-10">
        <p>🤖 AI đang đọc và tóm tắt...</p>
        <p class="text-sm italic">(Việc này có thể mất vài giây)</p>
      </div>
      
      <div v-else class="text-gray-700 space-y-2 whitespace-pre-line">
        {{ aiSummaryText }}
      </div>
      
      <div class="flex justify-end mt-5">
        <button
          @click="showAiSummaryModal = false"
          class="px-4 py-2 border border-gray-400 rounded-md text-gray-600 hover:bg-gray-100"
        >
          Đóng
        </button>
      </div>
    </div>
  </div>
</template>