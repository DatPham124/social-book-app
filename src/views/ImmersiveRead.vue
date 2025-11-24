<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'; // 1. Import onBeforeRouteLeave
import { useBooks } from '../composables/useBook';
import { COVER_IMAGE_SERVER_URL } from '../config';
import axios from 'axios';
import { BOOK_SERVICE_URL } from '../config';
import { useAuth } from '../composables/useAuth';

const route = useRoute();
const router = useRouter();
const { getBookById } = useBooks();
const { userInfo } = useAuth();

const bookId = Number(route.params.id);
const book = ref<any>(null);
const loading = ref(true);

// --- STATE CHO MODAL XÁC NHẬN THOÁT (MỚI) ---
const showExitModal = ref(false);
const pendingNextRoute = ref<Function | null>(null);
const isSavingOnExit = ref(false);

// --- CẤU HÌNH ÂM THANH (AMBIENCE) ---
const sounds = [
  { id: 'rain', name: 'Mưa rơi 🌧️', file: '/sounds/rain.mp3', color: 'from-gray-800 to-blue-900' },
  { id: 'cafe', name: 'White Noise ⚪', file: '/sounds/whitenoise.mp3', color: 'from-gray-500 to-slate-700' },
  { id: 'fireplace', name: 'Brown Noise 🟤', file: '/sounds/brownnoise.mp3', color: 'from-stone-800 to-stone-900' },
  { id: 'lofi', name: 'Nhạc Lofi 🎧', file: '/sounds/lofi.mp3', color: 'from-purple-900 to-indigo-900' },
  { id: 'off', name: 'Yên lặng 🔇', file: '', color: 'from-gray-900 to-black' }
];

const currentSoundId = ref('off');
const volume = ref(0.5);
const audioPlayer = ref<HTMLAudioElement | null>(null);

const currentSoundObj = computed(() => sounds.find(s => s.id === currentSoundId.value) || sounds[4]);

function changeSound(id: string) {
  currentSoundId.value = id;
  if (!audioPlayer.value) return;

  const sound = sounds.find(s => s.id === id);
  if (sound && sound.file) {
    audioPlayer.value.src = sound.file;
    audioPlayer.value.volume = volume.value;
    if (isRunning.value) {
        audioPlayer.value.play().catch(() => {});
    }
  } else {
    audioPlayer.value.pause();
    audioPlayer.value.src = "";
  }
}

watch(volume, (newVol) => {
  if (audioPlayer.value) audioPlayer.value.volume = newVol;
});

// --- CẤU HÌNH ĐỒNG HỒ (POMODORO) ---
const sessionMinutes = ref(25);
const timeLeft = ref(25 * 60); 
const isRunning = ref(false);
let timerInterval: any = null;

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

watch(sessionMinutes, (newVal) => {
  if (!isRunning.value) timeLeft.value = newVal * 60;
});

function toggleTimer() {
  if (isRunning.value) {
    // TẠM DỪNG
    clearInterval(timerInterval);
    isRunning.value = false;
    if (audioPlayer.value) audioPlayer.value.pause();
  } else {
    // BẮT ĐẦU
    isRunning.value = true;
    if (audioPlayer.value && currentSoundId.value !== 'off') {
        audioPlayer.value.play().catch(() => {});
    }
    timerInterval = setInterval(() => {
      if (timeLeft.value > 0) {
        timeLeft.value--;
      } else {
        clearInterval(timerInterval);
        isRunning.value = false;
        if (audioPlayer.value) audioPlayer.value.pause();
        alert("Ding! Hết phiên đọc sách.");
      }
    }, 1000);
  }
}

function resetTimer() {
  clearInterval(timerInterval);
  isRunning.value = false;
  timeLeft.value = sessionMinutes.value * 60;
  if (audioPlayer.value) audioPlayer.value.pause();
}

// --- CẬP NHẬT TIẾN ĐỘ ---
const currentPageInput = ref(0);

// Hàm update thường (có alert)
async function updatePageManual() {
    if (!userInfo.value || !book.value) return;
    try {
        await axios.put(
            `${BOOK_SERVICE_URL}books/reading-progress/${userInfo.value.user_id}/${book.value.id}`,
            null,
            { params: { current_page_from_user: currentPageInput.value } } 
        );
        alert("Đã cập nhật tiến độ!");
    } catch (e) {
        console.error(e);
        alert("Lỗi cập nhật.");
    }
}

// --- LOGIC CHẶN THOÁT (MỚI) ---
onBeforeRouteLeave((to, from, next) => {
  // Nếu có tiến độ nhập vào > 0, hỏi xác nhận
  if (currentPageInput.value > 0) {
      // Tạm dừng mọi thứ
      if (isRunning.value) toggleTimer();
      
      showExitModal.value = true;
      pendingNextRoute.value = next;
  } else {
      next();
  }
});

async function confirmExit(shouldSave: boolean) {
    if (shouldSave) {
        isSavingOnExit.value = true;
        // Gọi API update (không alert)
        if (userInfo.value && book.value) {
            try {
                await axios.put(
                    `${BOOK_SERVICE_URL}books/reading-progress/${userInfo.value.user_id}/${book.value.id}`,
                    null,
                    { params: { current_page_from_user: currentPageInput.value } } 
                );
            } catch (e) { console.error(e); }
        }
        isSavingOnExit.value = false;
    }
    
    showExitModal.value = false;
    if (pendingNextRoute.value) {
        pendingNextRoute.value(); // Cho phép chuyển trang
    }
}

function cancelExit() {
    showExitModal.value = false;
    pendingNextRoute.value = null;
}


// --- LIFECYCLE ---
onMounted(async () => {
  try {
    const [bookData, progressData] = await Promise.all([
        getBookById(bookId),
        userInfo.value ? axios.get(`${BOOK_SERVICE_URL}books/reading-progress/${userInfo.value.user_id}/${bookId}`) : Promise.resolve({data: null})
    ]);
    
    book.value = bookData;
    if (progressData.data) {
        currentPageInput.value = progressData.data.current_page;
    }

    if (book.value) {
      const cats = JSON.stringify(book.value.categories || []).toLowerCase();
      if (cats.includes('kinh dị') || cats.includes('trinh thám')) changeSound('rain');
      else if (cats.includes('học') || cats.includes('khoa học')) changeSound('cafe');
      else changeSound('fireplace');
    }
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
});

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval);
});

function exitMode() {
  router.back();
}
</script>

<template>
  <div 
    class="min-h-screen w-full flex flex-col items-center justify-center transition-colors duration-1000 ease-in-out relative overflow-hidden"
    :class="['bg-gradient-to-br', currentSoundObj.color]"
  >
    <audio ref="audioPlayer" loop></audio>

    <!-- Nút Thoát (Gọi router.back sẽ kích hoạt onBeforeRouteLeave) -->
    <button 
      @click="exitMode"
      class="absolute top-6 left-6 text-white/70 hover:text-white text-lg font-medium z-20 flex items-center gap-2"
    >
      &larr; Quay lại
    </button>

    <div v-if="loading" class="text-white">Đang tải không gian...</div>

    <div v-else class="z-10 w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 gap-12 items-center p-6">
      
      <!-- CỘT TRÁI: SÁCH & ĐỒNG HỒ -->
      <div class="flex flex-col items-center text-center space-y-8">
        <div class="relative group">
            <div class="absolute -inset-1 bg-gradient-to-r from-yellow-400 to-pink-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000"></div>
            <img 
              v-if="book.cover_url"
              :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" 
              class="relative w-56 h-auto rounded-lg shadow-2xl transform transition hover:scale-105 duration-500"
            />
            <div v-else class="relative w-56 h-80 bg-white/10 rounded-lg flex items-center justify-center text-4xl">📚</div>
        </div>

        <div class="text-white/90">
            <h1 class="text-3xl font-bold mb-2">{{ book.title }}</h1>
            <p class="text-lg opacity-75">{{ book.author }}</p>
        </div>

        <!-- Cập nhật trang thủ công -->
        <div class="flex items-center gap-2 bg-black/20 px-4 py-2 rounded-full backdrop-blur-sm border border-white/10">
            <span class="text-white/70 text-sm">Đang đọc trang:</span>
            <input 
                type="number" 
                v-model="currentPageInput" 
                class="w-16 bg-transparent text-white font-bold text-center border-b border-white/50 focus:border-yellow-400 outline-none"
            />
            <button @click="updatePageManual" class="text-yellow-400 hover:text-yellow-300 text-sm font-bold">Lưu</button>
        </div>
      </div>

      <!-- CỘT PHẢI: ĐIỀU KHIỂN -->
      <div class="space-y-8">
          
        <!-- Đồng hồ -->
        <div class="bg-white/10 backdrop-blur-md p-8 rounded-3xl border border-white/10 text-center">
            <div class="flex justify-center items-center gap-2 mb-4 text-white/60">
                <span>Hẹn giờ (phút):</span>
                <input type="number" v-model="sessionMinutes" :disabled="isRunning" class="w-12 bg-transparent border-b text-center font-bold text-white"/>
            </div>
            
            <div class="text-8xl font-mono font-thin text-white tracking-widest drop-shadow-lg mb-8">
                {{ formatTime(timeLeft) }}
            </div>

            <div class="flex justify-center gap-6">
                <button 
                    @click="toggleTimer"
                    class="px-8 py-3 rounded-full font-bold text-white shadow-lg transition transform hover:scale-105"
                    :class="isRunning ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'"
                >
                    {{ isRunning ? 'Tạm dừng' : 'Bắt đầu đọc' }}
                </button>
                <button @click="resetTimer" class="px-4 py-3 rounded-full bg-white/20 text-white hover:bg-white/30 font-bold">
                    ↺
                </button>
            </div>
        </div>

        <!-- Chọn Âm thanh -->
        <div class="bg-black/40 backdrop-blur-md p-6 rounded-3xl border border-white/10">
            <h3 class="text-white font-bold mb-4 flex items-center gap-2">
                <span>🎧</span> Không gian âm thanh
            </h3>
            <div class="grid grid-cols-2 gap-3">
                <button 
                    v-for="sound in sounds" 
                    :key="sound.id"
                    @click="changeSound(sound.id)"
                    class="p-3 rounded-xl text-left transition-all border"
                    :class="currentSoundId === sound.id 
                        ? 'bg-white/20 border-white/40 text-white shadow-inner' 
                        : 'bg-transparent border-transparent text-white/60 hover:bg-white/10 hover:text-white'"
                >
                    <div class="text-sm font-bold">{{ sound.name }}</div>
                    <div v-if="currentSoundId === sound.id && isRunning" class="text-[10px] text-green-400 mt-1 animate-pulse">Đang phát...</div>
                </button>
            </div>
            
            <div class="mt-6 flex items-center gap-3">
                <span class="text-white/60 text-xs">Volume</span>
                <input type="range" min="0" max="1" step="0.01" v-model="volume" class="flex-1 h-1 bg-white/20 rounded-lg appearance-none cursor-pointer accent-white">
            </div>
        </div>

      </div>

    </div>

    <!-- MODAL XÁC NHẬN THOÁT (MỚI) -->
    <div v-if="showExitModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-xl shadow-2xl max-w-md w-full p-6 text-gray-800">
            <h3 class="text-xl font-bold mb-2">Xác nhận rời phòng</h3>
            <p class="text-gray-600 mb-6">
                Bạn đang ở trang <strong>{{ currentPageInput }}</strong>. 
                Bạn có muốn lưu tiến độ đọc này trước khi thoát không?
            </p>
            
            <div class="flex flex-col gap-3">
                <button 
                    @click="confirmExit(true)"
                    :disabled="isSavingOnExit"
                    class="w-full py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-bold shadow transition flex justify-center items-center gap-2"
                >
                    <span v-if="isSavingOnExit" class="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></span>
                    Lưu tiến độ & Thoát
                </button>
                
                <button 
                    @click="confirmExit(false)"
                    class="w-full py-3 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-semibold transition"
                >
                    Thoát (Không lưu)
                </button>
                
                <button 
                    @click="cancelExit"
                    class="w-full py-2 text-sm text-gray-500 hover:text-gray-700 mt-2 underline"
                >
                    Hủy (Ở lại)
                </button>
            </div>
        </div>
    </div>

  </div>
</template>