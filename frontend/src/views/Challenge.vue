<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import Navbar from '../components/layout/Navbar.vue';
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from '../config';
import { useAuth } from '../composables/useAuth';
import axios from 'axios';

const { userInfo } = useAuth();
const userId = userInfo.value?.id || userInfo.value?.user_id;
const currentYear = new Date().getFullYear();

const loading = ref(true);
const hasJoined = ref(false);
const goal = ref(0);
const progress = ref(0);
const percentage = ref(0);
const readBooks = ref<any[]>([]);
const newGoalInput = ref(10); // Mặc định

async function loadChallenge() {
  if (!userId) return;
  loading.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}challenges/annual/${userId}/${currentYear}`);
    hasJoined.value = res.data.has_joined;
    
    if (hasJoined.value) {
      goal.value = res.data.goal;
      progress.value = res.data.progress;
      percentage.value = res.data.percentage;
      readBooks.value = res.data.read_books;
      newGoalInput.value = res.data.goal; // Để chỉnh sửa
    }
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
}

async function setGoal() {
  if (!userId) return;
  try {
    await axios.post(`${BOOK_SERVICE_URL}challenges/annual`, {
      user_id: userId,
      year: currentYear,
      goal_count: newGoalInput.value
    });
    // Tải lại để cập nhật giao diện
    await loadChallenge();
  } catch (err) {
    alert("Lỗi khi lưu mục tiêu");
  }
}

const progressColor = computed(() => {
  if (percentage.value < 30) return 'bg-red-500';
  if (percentage.value < 70) return 'bg-yellow-500';
  return 'bg-green-500';
});

onMounted(loadChallenge);
</script>

<template>
  <Navbar />
  <div class="w-full max-w-4xl mx-auto m-5 px-4">
    
    <h1 class="text-2xl font-logo text-yellow-400 item-center">
      Thử thách Đọc sách {{ currentYear }}
    </h1>

    <div v-if="loading" class="text-center py-10 text-gray-500">Đang tải...</div>

    <!-- TRẠNG THÁI A: CHƯA THAM GIA -->
    <div v-else-if="!hasJoined" class="bg-yellow-50 border border-yellow-200 rounded-xl p-8 text-center shadow-sm">
      <h2 class="text-2xl font-semibold text-yellow-800 mb-2">Bạn chưa đặt mục tiêu cho năm nay!</h2>
      <p class="text-gray-600 mb-6">Hãy đặt ra một con số để tạo động lực đọc sách nhé.</p>
      
      <div class="flex justify-center items-center gap-4">
        <span class="text-gray-700 font-medium">Tôi muốn đọc</span>
        <input 
          v-model.number="newGoalInput" 
          type="number" min="1" 
          class="w-20 p-2 border rounded text-center font-bold text-lg focus:ring-2 focus:ring-yellow-400 outline-none"
        />
        <span class="text-gray-700 font-medium">cuốn sách trong năm {{ currentYear }}.</span>
      </div>

      <button 
        @click="setGoal"
        class="mt-6 px-6 py-3 bg-yellow-400 hover:bg-yellow-500 text-black font-bold rounded-full transition transform hover:scale-105 shadow-md"
      >
        Bắt đầu Thử thách!
      </button>
    </div>

    <!-- TRẠNG THÁI B: ĐÃ THAM GIA (DASHBOARD) -->
    <div v-else class="space-y-8">
      
      <!-- 1. Thanh Tiến Độ -->
      <div class="bg-white p-6 rounded-xl shadow border border-gray-200">
        <div class="flex justify-between items-end mb-2">
          <div>
            <p class="text-sm text-gray-500">TIẾN ĐỘ CỦA BẠN</p>
            <p class="text-4xl font-bold text-gray-800">
              {{ progress }} <span class="text-xl text-gray-400 font-normal">/ {{ goal }} cuốn</span>
            </p>
          </div>
          <div class="text-right">
            <p class="text-2xl font-bold" :class="percentage >= 100 ? 'text-green-600' : 'text-gray-700'">
              {{ percentage }}%
            </p>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div 
            class="h-4 rounded-full transition-all duration-1000"
            :class="progressColor"
            :style="{ width: `${percentage}%` }"
          ></div>
        </div>

        <div class="mt-4 flex justify-between items-center">
          <p class="text-sm text-gray-600">
            <span v-if="percentage >= 100">🎉 Chúc mừng! Bạn đã hoàn thành thử thách!</span>
            <span v-else-if="percentage === 0">Hãy đọc cuốn sách đầu tiên để bắt đầu!</span>
            <span v-else>Cố lên! Bạn đang làm rất tốt.</span>
          </p>
          
          <!-- Chỉnh sửa mục tiêu -->
          <div class="flex items-center gap-2">
            <span class="text-xs text-gray-400">Sửa mục tiêu:</span>
            <input 
              v-model.number="newGoalInput" 
              type="number" min="1"
              class="w-16 p-1 border rounded text-xs text-center"
              @change="setGoal"
            />
          </div>
        </div>
      </div>

      <!-- 2. Kệ sách đã đọc trong năm (Bằng chứng) -->
      <div class="bg-white p-6 rounded-xl shadow border border-gray-200">
        <h3 class="font-semibold text-gray-800 mb-4 uppercase text-sm tracking-wide">Sách đã đọc trong năm {{ currentYear }}</h3>
        
        <div v-if="readBooks.length === 0" class="text-center py-8 text-gray-400 italic border-2 border-dashed rounded-lg">
          Chưa có cuốn sách nào được hoàn thành trong năm nay.
        </div>

        <div v-else class="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-4">
          <div v-for="book in readBooks" :key="book.id" class="group relative">
             <router-link :to="'/book/' + book.id">
                <img 
                  v-if="book.cover_url"
                  :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`"
                  class="w-full h-auto object-cover rounded shadow-md group-hover:shadow-xl transition-all duration-300 transform group-hover:-translate-y-1"
                  :title="book.title"
                />
                <div v-else class="w-full h-32 bg-gray-200 rounded flex items-center justify-center text-2xl">📚</div>
             </router-link>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>