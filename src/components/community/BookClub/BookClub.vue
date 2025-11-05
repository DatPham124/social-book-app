<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { debounce } from 'lodash'
import { BOOK_SERVICE_URL, USER_SERVICE_URL } from '../../../config'
import { useAuth } from '../../../composables/useAuth'

import BookClubList from "../BookClub/BookClubList.vue"
import BookClubForm from "../BookClub/BookClubForm.vue" 

interface Club {
  id: number;
  name: string;
  avatar_url?: string;
  description?: string;
  creator_id: number;
}

const { userInfo } = useAuth();
const userId = userInfo.value?.id || userInfo.value?.user_id;

const subTab = ref<'my_clubs' | 'discover'>('my_clubs');
const loading = ref(false);
const error = ref<string | null>(null);

const myClubs = ref<Club[]>([]);
const loadingMyClubs = ref(false);

const discoverClubs = ref<Club[]>([]);
const loadingDiscover = ref(false);
const searchQuery = ref("");

const creatingClub = ref(false);

async function loadMyClubs() {
  if (!userId) {
    error.value = "Lỗi xác thực người dùng.";
    return;
  }
  loadingMyClubs.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/joined_by/${userId}`);
    myClubs.value = res.data;
  } catch (err: any) {
    if (err.response?.status !== 404) {
      error.value = "Không thể tải câu lạc bộ của bạn.";
    }
    myClubs.value = [];
  } finally {
    loadingMyClubs.value = false;
  }
}

const loadDiscoverClubs = async () => {
  if (!searchQuery.value.trim()) {
    discoverClubs.value = [];
    return;
  }
  
  loadingDiscover.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/search`, {
      params: { q: searchQuery.value }
    });
    discoverClubs.value = res.data;
  } catch (err) {
    console.error("Lỗi tìm kiếm clubs:", err);
  } finally {
    loadingDiscover.value = false;
  }
};

const debouncedSearch = debounce(loadDiscoverClubs, 300);
watch(searchQuery, debouncedSearch);

onMounted(loadMyClubs);

function startCreate() {
  creatingClub.value = true
}
function handleCancel() {
  creatingClub.value = false
}
function handleSaved(club: any) {
  creatingClub.value = false
  loadMyClubs();
  subTab.value = 'my_clubs';
}
</script>

<template>
  <BookClubForm
    v-if="creatingClub"
    @saved="handleSaved"
    @cancel="handleCancel"
    class="w-full max-w-2xl mx-auto"
  />

  <div v-else class="w-full max-w-5xl mx-auto">
    <div class="flex justify-end mb-4">
      <button
        @click="startCreate"
        class="bg-yellow-400 hover:bg-yellow-500 text-black font-semibold px-4 py-2 rounded-md transition"
      >
        + Tạo Câu Lạc Bộ Mới
      </button>
    </div>

    <div class="flex gap-6 border-b border-gray-300 mb-6">
      <button 
        @click="subTab = 'my_clubs'"
        class="relative pb-2 font-medium transition-colors duration-200"
        :class="subTab === 'my_clubs' ? 'text-yellow-500' : 'text-gray-500 hover:text-gray-800'"
      >
        Câu lạc bộ của tôi
        <span v-if="subTab === 'my_clubs'" class="absolute left-0 bottom-0 w-full h-[2px] bg-yellow-400"></span>
      </button>
      <button 
        @click="subTab = 'discover'"
        class="relative pb-2 font-medium transition-colors duration-200"
        :class="subTab === 'discover' ? 'text-yellow-500' : 'text-gray-500 hover:text-gray-800'"
      >
        Khám phá
        <span v-if="subTab === 'discover'" class="absolute left-0 bottom-0 w-full h-[2px] bg-yellow-400"></span>
      </button>
    </div>

    <div v-if="subTab === 'my_clubs'">
      <div v-if="loadingMyClubs" class="text-center text-gray-500 py-10">
        Đang tải...
      </div>
      <div v-else-if="myClubs.length === 0" class="text-center text-gray-500 py-10">
        Bạn chưa tham gia câu lạc bộ nào.
      </div>
      <BookClubList v-else :clubs="myClubs" />
    </div>

    <div v-if="subTab === 'discover'">
      <input 
        v-model="searchQuery"
        type="text"
        class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none mb-6"
        placeholder="Tìm câu lạc bộ công khai theo tên..."
      />
      <div v-if="loadingDiscover" class="text-center text-gray-500 py-10">
        Đang tìm...
      </div>
      <div v-else-if="discoverClubs.length === 0 && searchQuery" class="text-center text-gray-500 py-10">
        Không tìm thấy kết quả nào cho "{{ searchQuery }}".
      </div>
      <BookClubList v-else :clubs="discoverClubs" />
    </div>

  </div>
</template>

