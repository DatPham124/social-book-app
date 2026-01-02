<script setup lang="ts">
import { ref, onMounted, Ref } from "vue";
import axios from "axios";
import { BOOK_SERVICE_URL, USER_SERVICE_URL, COVER_IMAGE_SERVER_URL, AVATAR_SERVER_URL } from "../../../config";
import { useAuth } from "../../../composables/useAuth";
import { useBookSearch } from "../../../composables/useBookSearch";
import { getProfile } from "../../../composables/useProfile"; // Import getProfile

const emit = defineEmits(["created", "cancel"]);
const { userInfo } = useAuth();
const { query, results, searchBooks } = useBookSearch() as {
  query: Ref<string>;
  results: Ref<any[]>;
  searchBooks: () => Promise<void>;
};

// Interface cho các model
interface Book {
  id: number;
  title: string;
  cover_url?: string;
}
interface Friend {
  id: number; // Đây là ID của bản ghi Friends
  user_id: number;
  friend_id: number;
  profile?: { // Sẽ được gộp vào
    user_id: number;
    username: string;
    avatar_url?: string;
  }
}

// State
const selectedBook = ref<Book | null>(null);
const friendsList = ref<Friend[]>([]);
const selectedFriendIds = ref<number[]>([]);
const loading = ref(false);
const message = ref("");

// Lấy danh sách bạn bè từ user-service
async function loadFriends() {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  const token = localStorage.getItem("token");
  if (!userId || !token) return;

  try {
    // API GET /{user_id}/{status} từ friend.py
    const res = await axios.get(
      `${USER_SERVICE_URL}friends/${userId}/accepted`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    
    // Gộp thông tin profile
    const friendsWithProfile = await Promise.all(
      res.data.map(async (friend: Friend) => {
        // Tìm ID của người bạn (không phải ID của mình)
        const friendProfileId = friend.user_id === userId ? friend.friend_id : friend.user_id;
        // Dùng getProfile (an toàn hơn, có try/catch)
        const profile = await getProfile(friendProfileId); 
        return { ...friend, profile: profile };
      })
    );
    friendsList.value = friendsWithProfile;
    
  } catch (error) {
    console.error("Lỗi khi tải danh sách bạn bè:", error);
  }
}

function handleSelectBook(book: Book) {
  selectedBook.value = book;
  query.value = book.title;
  results.value = [];
}

async function createBuddyRead() {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId || !selectedBook.value) {
    message.value = "Vui lòng chọn sách và đăng nhập.";
    return;
  }

  loading.value = true;
  message.value = "";
  
  try {
    const formData = new FormData();
    formData.append("book_id", String(selectedBook.value.id));
    formData.append("user_id", String(userId));
    // Gửi danh sách ID bạn bè dưới dạng JSON string
    formData.append("friend_ids_json", JSON.stringify(selectedFriendIds.value));

    // Gọi API (Bước 2, Route 1)
    await axios.post(
      `${BOOK_SERVICE_URL}buddyreads/create`, 
      formData
    );
    
    emit("created"); // Báo cho cha (Community.vue) biết đã tạo xong

  } catch (err: any) {
    message.value = err.response?.data?.detail || "Tạo thất bại";
  } finally {
    loading.value = false;
  }
}

onMounted(loadFriends);
</script>

<template>
  <div class="p-6 border rounded-lg bg-gray-50">
    <h3 class="text-lg font-semibold mb-4 text-gray-700">Tạo Đọc Cùng Bạn</h3>
    
    <!-- 1. Chọn Sách -->
    <div class="space-y-4">
      <div v-if="!selectedBook">
        <label class="block text-sm font-medium text-gray-600 mb-1">Chọn một cuốn sách</label>
        <input 
          v-model="query" 
          @input="searchBooks" 
          type="text" 
          class="w-full border rounded-md px-3 py-2"
          placeholder="Tìm sách..." 
        />
        <ul v-if="results.length" class="border rounded-md mt-2 bg-white shadow-sm max-h-48 overflow-y-auto z-10">
          <li v-for="book in results" :key="book.id" @click="handleSelectBook(book)"
            class="px-3 py-2 hover:bg-yellow-50 cursor-pointer flex items-center gap-3">
            <img 
              v-if="book.cover_url"
              :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" 
              class="w-8 h-12 object-cover rounded" 
            />
            <div v-else class="w-8 h-12 bg-gray-200 rounded flex items-center justify-center">📚</div>
            <span>{{ book.title }}</span>
          </li>
        </ul>
      </div>
      
      <!-- Sách đã chọn -->
      <div v-else class="flex gap-3 bg-white p-3 rounded-lg border">
        <img 
          v-if="selectedBook.cover_url"
          :src="`${COVER_IMAGE_SERVER_URL}/${selectedBook.cover_url}`" 
          class="w-12 h-16 object-cover rounded" 
        />
        <div v-else class="w-12 h-16 bg-gray-200 rounded flex items-center justify-center">📚</div>
        <div>
          <p class="font-semibold text-gray-800">{{ selectedBook.title }}</p>
          <button @click="selectedBook = null; query = ''" class="text-sm text-red-500 hover:underline">
            Chọn sách khác
          </button>
        </div>
      </div>

      <!-- 2. Mời Bạn bè -->
      <div v-if="selectedBook">
        <label class="block text-sm font-medium text-gray-600 mb-2">Mời bạn bè (Không bắt buộc)</label>
        <div v-if="friendsList.length === 0" class="text-sm text-gray-500 italic">
          Bạn chưa có người bạn nào.
        </div>
        <div v-else class="space-y-2 max-h-48 overflow-y-auto p-2 bg-white rounded-md border">
          
          <template v-for="friend in friendsList" :key="friend.id">
            <label 
              v-if="friend.profile" 
              class="flex items-center gap-3 p-2 hover:bg-gray-50 rounded cursor-pointer"
            >
              <input 
                type="checkbox" 
                :value="friend.profile.user_id" 
                v-model="selectedFriendIds"
                class="h-4 w-4 text-yellow-500 border-gray-300 rounded focus:ring-yellow-400"
              />
              <img 
                v-if="friend.profile.avatar_url"
                :src="`${AVATAR_SERVER_URL}/${friend.profile.avatar_url}`" 
                class="w-8 h-8 rounded-full object-cover" 
              />
              <div v-else class="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-sm font-bold">
                {{ friend.profile.username?.charAt(0).toUpperCase() }}
              </div>
              <span class="text-gray-700">{{ friend.profile.username }}</span>
            </label>
          </template>
        </div>
      </div>

      <p v-if="message" class="text-sm text-red-500">{{ message }}</p>

      <!-- 3. Nút Bấm -->
      <div class="flex justify-end space-x-3 mt-4">
        <button @click="$emit('cancel')" class="px-4 py-2 border rounded-md text-gray-600 hover:bg-gray-100">
          Hủy
        </button>
        <button 
          @click="createBuddyRead" 
          :disabled="loading || !selectedBook"
          class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 rounded-md font-semibold disabled:opacity-50"
        >
          {{ loading ? 'Đang tạo...' : 'Tạo phòng đọc' }}
        </button>
      </div>
    </div>
  </div>
</template>

