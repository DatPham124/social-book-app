<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed, watch } from 'vue';
import Navbar from '../components/layout/Navbar.vue';
import { useAuth } from '../composables/useAuth';
import { AVATAR_SERVER_URL, BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL, AUDIO_SERVER_URL } from '../config';
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'; // Thêm onBeforeRouteLeave
import axios from 'axios';
import { useBooks } from '../composables/useBook';

// ... (Firebase Imports & Config giữ nguyên) ...
import { initializeApp } from "firebase/app";
import { 
  getFirestore, collection, addDoc, query, orderBy, limit, onSnapshot, 
  serverTimestamp, doc, setDoc, deleteDoc, getDocs, writeBatch
} from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyBBwx33GoMKb1PgXgTsdxJDL9YQmTHAz1I",
  authDomain: "realtime-6cee8.firebaseapp.com",
  projectId: "realtime-6cee8",
  storageBucket: "realtime-6cee8.firebasestorage.app",
  messagingSenderId: "680063110664",
  appId: "1:680063110664:web:75de42784c4d3a79828bbd"
};

const props = withDefaults(defineProps<{
  mode?: 'group' | 'solo';
}>(), { mode: 'group' });

let app: any = null;
let db: any = null;
if (props.mode === 'group') {
    app = initializeApp(firebaseConfig);
    db = getFirestore(app);
}

const route = useRoute();
const router = useRouter();
const { userInfo } = useAuth();
const { getBookById } = useBooks();

// --- STATE ---
const currentBook = ref<any>(null);
const audioChapters = ref<any[]>([]); 
const currentChapterIndex = ref(0);   
const isAudioBook = computed(() => audioChapters.value.length > 0);

const audioPlayer = ref<HTMLAudioElement | null>(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);

const calculatedPage = ref(0);
let progressUpdateTimeout: any = null;

// STATE CHO MODAL XÁC NHẬN THOÁT
const showExitModal = ref(false);
const pendingNextRoute = ref<Function | null>(null);
const isSavingOnExit = ref(false);

// ... (State Pomodoro, Firebase, Chat giữ nguyên) ...
const messages = ref<any[]>([]);
const onlineUsers = ref<any[]>([]);
const newMessage = ref("");
const chatContainer = ref<HTMLElement | null>(null);
const roomId = props.mode === 'group' ? `buddy_${route.params.id}` : `solo_${userInfo.value?.user_id}_${route.params.id}`;
const timeLeft = ref(25 * 60);
const isRunning = ref(false);
const currentMode = ref<'focus' | 'break'>('focus');
let timerInterval: any = null;
let unsubscribeMessages: any = null;
let unsubscribeUsers: any = null;

// --- LOGIC TẢI DỮ LIỆU ---
async function loadBookInfo() {
    try {
        let targetBookId = 0;
        if (props.mode === 'group') {
             const brRes = await axios.get(`${BOOK_SERVICE_URL}buddyreads/${route.params.id}`);
             targetBookId = brRes.data.book_id;
        } else {
             targetBookId = Number(route.params.id);
        }
        
        const res = await axios.get(`${BOOK_SERVICE_URL}books/${targetBookId}/details`);
        currentBook.value = res.data;
        audioChapters.value = (res.data.audios || []).sort((a: any, b: any) => a.order - b.order);
        
    } catch (error) {
        console.error("Lỗi tải sách:", error);
    }
}

// --- LOGIC XỬ LÝ AUDIO ĐA PHẦN (MULTI-PART) ---

const currentAudioSrc = computed(() => {
    if (!audioChapters.value.length) return "";
    return `${AUDIO_SERVER_URL}/${audioChapters.value[currentChapterIndex.value].file_url}`;
});

function playPause() {
    if (!audioPlayer.value) return;
    if (isPlaying.value) audioPlayer.value.pause();
    else audioPlayer.value.play();
}

function selectChapter(index: number) {
    if (index < 0 || index >= audioChapters.value.length) return;
    
    currentChapterIndex.value = index;
    nextTick(() => {
        if(audioPlayer.value) {
            audioPlayer.value.load(); 
            audioPlayer.value.play(); 
            isPlaying.value = true;
        }
    });
}

function onAudioEnded() {
    if (currentChapterIndex.value < audioChapters.value.length - 1) {
        selectChapter(currentChapterIndex.value + 1);
    } else {
        isPlaying.value = false;
        alert("Chúc mừng! Bạn đã nghe hết cuốn sách.");
        if (currentBook.value) {
            // Cập nhật ngay lập tức khi hết sách
            sendProgressUpdate(currentBook.value.page_count);
        }
    }
}

// Cập nhật thanh thời gian & Tiến độ đọc
function onTimeUpdate() {
    if (!audioPlayer.value || !currentBook.value || !currentBook.value.page_count) return;
    
    currentTime.value = audioPlayer.value.currentTime;
    duration.value = audioPlayer.value.duration;
    
    if (duration.value > 0) {
         const totalChapters = audioChapters.value.length;
         const percentOfCurrentChapter = currentTime.value / duration.value; 
         
         const totalProgressPercent = (currentChapterIndex.value + percentOfCurrentChapter) / totalChapters;
         
         const newPage = Math.round(totalProgressPercent * currentBook.value.page_count);
         
         if (newPage !== calculatedPage.value) {
             calculatedPage.value = newPage;
             scheduleProgressUpdate(newPage);
         }
    }
}

// Gửi API ngay lập tức (Dùng cho nút Save & Exit)
async function sendProgressUpdate(page: number) {
    if (!userInfo.value || !currentBook.value) return;
    console.log(`[Immediate Update] Cập nhật tiến độ: Trang ${page}`);
    try {
        await axios.put(
            `${BOOK_SERVICE_URL}books/reading-progress/${userInfo.value.user_id}/${currentBook.value.id}`,
            null,
            { params: { current_page_from_user: page } } 
        );
    } catch (e) {
        console.error("Lỗi update:", e);
    }
}

// Gửi API có độ trễ (Dùng khi đang nghe)
function scheduleProgressUpdate(page: number) {
    if (progressUpdateTimeout) clearTimeout(progressUpdateTimeout);
    
    progressUpdateTimeout = setTimeout(() => {
        console.log(`[Auto-Update] Đang cập nhật tiến độ: Trang ${page}`);
        sendProgressUpdate(page);
    }, 10000); 
}

const formatTimeAudio = (s: number) => {
    if (isNaN(s)) return "00:00";
    const min = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${min}:${sec < 10 ? '0' + sec : sec}`;
}

// --- GUARD: CHẶN THOÁT & HỎI XÁC NHẬN ---
onBeforeRouteLeave((to, from, next) => {
  // Chỉ hỏi khi: Đang nghe Audio VÀ đã có tiến độ tính được > 0
  if (isAudioBook.value && calculatedPage.value > 0) {
      // Tạm dừng nhạc
      if (audioPlayer.value) audioPlayer.value.pause();
      isPlaying.value = false;

      // Hiển thị Modal
      showExitModal.value = true;
      
      // Lưu lại hàm next để gọi sau khi user chọn
      pendingNextRoute.value = next;
      
      // Chặn chuyển trang tạm thời
      // (Lưu ý: Vue Router next(false) có thể không hoạt động như mong đợi trong composition API async
      // nhưng việc không gọi next() sẽ chặn lại)
  } else {
      next();
  }
});

// Xử lý khi chọn trong Modal
async function confirmExit(shouldSave: boolean) {
    if (shouldSave) {
        isSavingOnExit.value = true;
        await sendProgressUpdate(calculatedPage.value);
        isSavingOnExit.value = false;
    }
    
    showExitModal.value = false;
    if (pendingNextRoute.value) {
        pendingNextRoute.value(); // Tiếp tục chuyển trang
    }
}

function cancelExit() {
    showExitModal.value = false;
    pendingNextRoute.value = null;
    // User chọn ở lại -> Có thể play nhạc lại nếu muốn
}

// ... (Logic Pomodoro, Firebase, Lifecycle giữ nguyên) ...
const formatTimePomodoro = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
};
function toggleTimer() {
    if (isRunning.value) {
        clearInterval(timerInterval);
        isRunning.value = false;
        if (props.mode === 'group') updateUserStatus("paused");
    } else {
        isRunning.value = true;
        if (props.mode === 'group') updateUserStatus(currentMode.value);
        timerInterval = setInterval(() => {
            if (timeLeft.value > 0) timeLeft.value--;
            else {
                clearInterval(timerInterval);
                isRunning.value = false;
                if (props.mode === 'group') updateUserStatus("idle");
            }
        }, 1000);
    }
}
async function updateUserStatus(status: string) {
    if (!userInfo.value || !db) return;
    const userRef = doc(db, "rooms", roomId, "users", String(userInfo.value.user_id));
    try {
        await setDoc(userRef, {
            id: userInfo.value.user_id, username: userInfo.value.username, avatar: userInfo.value.avatar_url,
            status: status, last_active: serverTimestamp()
        }, { merge: true });
    } catch (e) { console.error(e); }
}
async function sendMessage() {
     if (!newMessage.value.trim() || !userInfo.value || !db) return;
     try {
        await addDoc(collection(db, "rooms", roomId, "messages"), {
            text: newMessage.value, user_id: userInfo.value.user_id, username: userInfo.value.username,
            avatar: userInfo.value.avatar_url, created_at: serverTimestamp()
        });
        newMessage.value = "";
     } catch (e) { console.error(e); }
}

onMounted(async () => {
    if (!userInfo.value) { router.push('/login'); return; }
    await loadBookInfo();

    if (props.mode === 'group' && db) {
        updateUserStatus(isAudioBook.value ? "listening" : "idle");
        const usersQ = query(collection(db, "rooms", roomId, "users"));
        unsubscribeUsers = onSnapshot(usersQ, (snap) => onlineUsers.value = snap.docs.map(d => d.data()));
        const msgQ = query(collection(db, "rooms", roomId, "messages"), orderBy("created_at", "asc"), limit(100));
        unsubscribeMessages = onSnapshot(msgQ, (snap) => {
             messages.value = snap.docs.map(d => ({id: d.id, ...d.data()}));
             nextTick(() => chatContainer.value && (chatContainer.value.scrollTop = chatContainer.value.scrollHeight));
        });
    }
});

onUnmounted(() => {
    if (timerInterval) clearInterval(timerInterval);
    if (unsubscribeMessages) unsubscribeMessages();
    if (unsubscribeUsers) unsubscribeUsers();
});

function goBack() { router.back(); }

function seekAudio(event: Event) {
    const target = event.target as HTMLInputElement;
    if (audioPlayer.value && target) {
        audioPlayer.value.currentTime = Number(target.value);
    }
}
</script>

<template>
  <Navbar />

  <div class="max-w-7xl mx-auto p-4 md:p-6 h-[calc(100vh-80px)]">
    
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
        <button @click="goBack" class="text-gray-600 hover:text-yellow-600 font-medium flex items-center gap-2">
            &larr; {{ props.mode === 'group' ? 'Rời phòng nhóm' : 'Quay lại sách' }}
        </button>
        
        <div class="flex items-center gap-2">
             <div class="text-sm text-gray-500 italic" v-if="currentBook">
                Đang nghe: <span class="font-bold text-gray-700">{{ currentBook.title }}</span>
            </div>
             <div v-if="props.mode === 'group'" class="flex items-center gap-1 bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded-full">
                <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                {{ onlineUsers.length }} Online
             </div>
        </div>
    </div>

    <div class="grid gap-6 h-full pb-10" 
         :class="props.mode === 'group' ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1 max-w-3xl mx-auto'">
        
        <!-- CỘT TRÁI (PLAYER & ĐỒNG HỒ) -->
        <div class="flex flex-col gap-6" :class="props.mode === 'group' ? 'lg:col-span-2' : 'w-full'">
            
            <!-- === GIAO DIỆN 1: MÁY NGHE NHẠC (AUDIO) === -->
            <div v-if="isAudioBook" class="flex-1 bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-2xl p-6 text-white flex flex-col overflow-hidden">
                
                <!-- Phần trên: Ảnh bìa + Thông tin -->
                <div class="flex gap-6 items-start mb-6">
                    <div class="relative flex-shrink-0">
                         <img v-if="currentBook?.cover_url" 
                              :src="`${COVER_IMAGE_SERVER_URL}/${currentBook.cover_url}`" 
                              class="w-28 h-40 object-cover rounded-lg shadow-lg border border-white/10" 
                              :class="isPlaying ? 'animate-pulse' : ''" />
                         <div v-else class="w-28 h-40 bg-white/10 rounded flex items-center justify-center text-2xl">📚</div>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h2 class="text-xl font-bold mb-1 truncate">{{ currentBook?.title }}</h2>
                        <p class="text-sm text-gray-400 mb-3">{{ currentBook?.author }}</p>
                        
                        <div class="bg-white/10 rounded-lg p-3 backdrop-blur-sm border border-white/5">
                            <p class="text-xs text-gray-400 uppercase tracking-wider mb-1">Đang phát</p>
                            <p class="text-sm font-semibold text-green-400 truncate">
                                {{ audioChapters[currentChapterIndex]?.title || 'Đang tải...' }}
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Phần giữa: Danh sách phát (Playlist) -->
                <div class="flex-1 bg-black/20 rounded-lg border border-white/5 overflow-hidden flex flex-col mb-4">
                    <div class="p-3 border-b border-white/10 text-xs font-bold text-gray-400 uppercase">
                        Danh sách chương ({{ audioChapters.length }})
                    </div>
                    <div class="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                        <div 
                            v-for="(chapter, idx) in audioChapters" 
                            :key="chapter.id"
                            @click="selectChapter(idx)"
                            class="p-3 rounded cursor-pointer flex items-center gap-3 transition-colors group"
                            :class="idx === currentChapterIndex ? 'bg-green-500/20 border border-green-500/30' : 'hover:bg-white/5 border border-transparent'"
                        >
                            <div class="text-xs font-mono w-6 text-right" :class="idx === currentChapterIndex ? 'text-green-400' : 'text-gray-500'">
                                {{ idx + 1 }}
                            </div>
                            <div class="flex-1 text-sm truncate" :class="idx === currentChapterIndex ? 'text-white font-medium' : 'text-gray-300 group-hover:text-white'">
                                {{ chapter.title }}
                            </div>
                            <div v-if="idx === currentChapterIndex" class="text-green-400 text-xs animate-pulse">
                                🎵
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Phần dưới: Thanh điều khiển -->
                <div class="mt-auto">
                    <div class="flex justify-between text-xs text-gray-400 mb-2">
                        <span>{{ formatTimeAudio(currentTime) }}</span>
                        <span>{{ formatTimeAudio(duration) }}</span>
                    </div>
                    
                    <input type="range" min="0" :max="duration" v-model="currentTime" 
                           class="w-full h-1.5 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500 mb-6 hover:h-2 transition-all"
                           @input="seekAudio">

                    <div class="flex justify-center items-center gap-8">
                        <button @click="selectChapter(Math.max(0, currentChapterIndex - 1))" 
                                :disabled="currentChapterIndex === 0"
                                class="text-2xl text-gray-400 hover:text-white disabled:opacity-30 transition">
                            ⏮
                        </button>
                        
                        <button @click="playPause" 
                                class="w-14 h-14 bg-white text-black rounded-full flex items-center justify-center text-2xl hover:scale-110 hover:bg-green-400 transition shadow-lg shadow-green-900/20">
                            {{ isPlaying ? '⏸' : '▶' }}
                        </button>
                        
                        <button @click="selectChapter(Math.min(audioChapters.length - 1, currentChapterIndex + 1))" 
                                :disabled="currentChapterIndex === audioChapters.length - 1"
                                class="text-2xl text-gray-400 hover:text-white disabled:opacity-30 transition">
                            ⏭
                        </button>
                    </div>
                    
                     <div class="text-center mt-4">
                         <span v-if="calculatedPage > 0" class="text-xs text-green-300/80 font-mono">
                            Tiến độ dự kiến: Trang {{ calculatedPage }}
                         </span>
                     </div>
                </div>

                <audio ref="audioPlayer" 
                       :src="currentAudioSrc" 
                       @timeupdate="onTimeUpdate"
                       @ended="onAudioEnded"
                       @play="isPlaying = true"
                       @pause="isPlaying = false"
                       hidden>
                </audio>
            </div>

            <!-- === GIAO DIỆN 2: ĐỒNG HỒ (GIỮ NGUYÊN) === -->
            <div v-else class="bg-white rounded-2xl shadow-lg border p-10 text-center flex flex-col items-center justify-center flex-1 relative">
                <h2 class="text-gray-500 font-bold tracking-widest mb-6">POMODORO TIMER</h2>
                <div class="text-9xl font-mono font-bold text-gray-800 mb-8">{{ formatTimePomodoro(timeLeft) }}</div>
                <button @click="toggleTimer" class="px-10 py-4 bg-indigo-600 text-white rounded-full font-bold text-lg hover:bg-indigo-700">
                    {{ isRunning ? 'Tạm dừng' : 'Bắt đầu đọc' }}
                </button>
                <p class="mt-4 text-gray-400 text-sm italic">(Sách này chưa có Audio)</p>
            </div>
            
        </div>

        <!-- CỘT PHẢI: CHAT (CHỈ HIỆN KHI LÀ GROUP) -->
        <div v-if="props.mode === 'group'" class="flex flex-col bg-white rounded-2xl shadow-lg border overflow-hidden h-full">
             <div class="p-4 border-b font-bold text-gray-700">💬 Chat Nhóm</div>
             <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
                 <div v-for="msg in messages" :key="msg.id" class="p-2 bg-gray-100 rounded-lg text-sm">
                     <span class="font-bold">{{ msg.username }}:</span> {{ msg.text }}
                 </div>
             </div>
             <div class="p-3 border-t bg-gray-50">
                 <form @submit.prevent="sendMessage" class="flex gap-2">
                     <input v-model="newMessage" class="flex-1 border rounded-full px-3 py-2 text-sm" placeholder="Chat..." />
                 </form>
             </div>
        </div>

    </div>

    <!-- MODAL XÁC NHẬN THOÁT -->
    <div v-if="showExitModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-xl shadow-2xl max-w-md w-full p-6">
            <h3 class="text-xl font-bold text-gray-800 mb-2">Xác nhận rời phòng</h3>
            <p class="text-gray-600 mb-6">
                Bạn đang ở trang <strong>{{ calculatedPage }}</strong>. 
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
                    Hủy
                </button>
            </div>
        </div>
    </div>

  </div>
</template>