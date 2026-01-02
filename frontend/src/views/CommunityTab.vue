<script setup lang="ts">
import { ref, onMounted, Ref } from 'vue' 
import Navbar from '../components/layout/Navbar.vue'
import BookClub from '../components/community/BookClub/BookClub.vue'
import UpdateStatusBox from '../components/community/NewFeed/UpdateStatusBox.vue'
import ActivityFeed from '../components/community/NewFeed/ActivityFeed.vue'
import CreateBuddyRead from '../components/community/BuddyRead/CreateBuddyRead.vue'; 

import axios from 'axios' 
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from '../config'
import { useAuth } from '../composables/useAuth'
import { useBooks } from '../composables/useBook' // <-- SỬA LỖI TYPO 'useBook'

// --- State cho Buddy Reads ---
interface BuddyRead {
  id: number;
  book_id: number;
  book?: { title: string, cover_url: string }; // Sẽ gộp vào
}
const buddyReadsList = ref<BuddyRead[]>([]);
const showCreateBuddyRead = ref(false);
const isLoadingBuddyReads = ref(false);
const { userInfo } = useAuth();
const { getBookById } = useBooks();
// ---

const tabs = [
  { name: 'Bản Tin', value: 'newsfeed' },
  { name: 'Đọc Cùng Bạn', value: 'buddyreads' },
  { name: 'Câu Lạc Bộ Sách', value: 'bookclubs' },
]

const activeTab = ref('newsfeed')

function selectTab(tabValue: string) {
  activeTab.value = tabValue
  // Nếu chuyển qua tab buddy reads, tải dữ liệu
  if (tabValue === 'buddyreads' && buddyReadsList.value.length === 0) {
    loadBuddyReads();
  }
}

// 2. THÊM HÀM LẤY DANH SÁCH BUDDY READS
async function loadBuddyReads() {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId) return;

  isLoadingBuddyReads.value = true;
  try {
    // Gọi API (Bước 2, Route 2)
    const res = await axios.get(`${BOOK_SERVICE_URL}buddyreads/user/${userId}`);
    
    // Lấy chi tiết sách cho mỗi read
    const readsWithBook = await Promise.all(
      res.data.map(async (read: BuddyRead) => {
        const book = await getBookById(read.book_id);
        return { ...read, book: book };
      })
    );
    buddyReadsList.value = readsWithBook;

  } catch (error) {
    console.error("Lỗi tải buddy reads:", error);
  } finally {
    isLoadingBuddyReads.value = false;
  }
}

function handleBuddyReadCreated() {
  showCreateBuddyRead.value = false;
  loadBuddyReads(); // Tải lại danh sách
}

onMounted(() => {
  // Tải data cho tab mặc định
  if (activeTab.value === 'buddyreads') {
    loadBuddyReads();
  }
});
</script>

<template>
  <Navbar />

  <div class="w-full max-w-5xl mx-auto m-5 space-y-6 px-4">
    <h1 class="text-2xl font-logo text-yellow-400 item-center">Cộng đồng</h1>

    <div class="flex flex-wrap gap-6 border-b border-gray-300">
      <button v-for="tab in tabs" :key="tab.value" @click="selectTab(tab.value)"
        class="relative pb-2 text-gray-600 hover:text-yellow-400 font-medium transition-colors duration-200">
        <span>{{ tab.name }}</span>
        <span v-if="activeTab === tab.value"
          class="absolute left-0 bottom-0 w-full h-[2px] bg-yellow-400 rounded-full "></span>
      </button>
    </div>

    <!-- Nội dung tab -->
    <div class="mt-8">
      
      <div v-if="activeTab === 'newsfeed'">
        <UpdateStatusBox />
        <ActivityFeed />
      </div>

      <!-- 3. THÊM NỘI DUNG TAB "ĐỌC CÙNG BẠN" -->
      <div v-else-if="activeTab === 'buddyreads'">
        <!-- Hiển thị Form -->
        <div v-if="showCreateBuddyRead">
          <CreateBuddyRead @created="handleBuddyReadCreated" @cancel="showCreateBuddyRead = false" />
        </div>
        
        <!-- Hiển thị Danh sách -->
        <div v-else>
          <div class="flex justify-end mb-4">
            <button @click="showCreateBuddyRead = true"
              class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md transition">
              + Tạo Đọc Cùng Bạn
            </button>
          </div>
          
          <div v-if="isLoadingBuddyReads" class="text-center text-gray-500 py-10">
            Đang tải...
          </div>
          <div v-else-if="buddyReadsList.length === 0" class="text-center text-gray-500 py-10">
            Bạn chưa tham gia phòng đọc nào.
          </div>
          
          <!-- Danh sách các phòng đọc -->
          <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <router-link 
              v-for="read in buddyReadsList" 
              :key="read.id"
              :to="'/buddy-read/' + read.id"
              class="block bg-white p-4 rounded-lg border shadow-sm hover:shadow-md transition"
            >
              
              <!-- === SỬA LẠI PHẦN HIỂN THỊ ẢNH === -->
              <div class="w-full h-48 bg-gray-100 rounded mb-3 flex items-center justify-center overflow-hidden">
                <img 
                  v-if="read.book?.cover_url"
                  :src="`${COVER_IMAGE_SERVER_URL}/${read.book.cover_url}`"
                  :alt="read.book.title"
                  class="w-full h-full object-contain"
                />
                <!-- Sửa lại placeholder -->
                <div v-else class="text-4xl text-gray-400">📚</div>
              </div>
              
              <h3 class="font-semibold text-gray-800 truncate">{{ read.book?.title }}</h3>
              <!-- Sửa lại text (vì chưa lấy được số lượng bạn) -->
              <p class="text-sm text-gray-500">Nhấn để xem chi tiết</p>
            </router-link>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'bookclubs'">
        <BookClub />
      </div>

    </div>
  </div>
</template>
