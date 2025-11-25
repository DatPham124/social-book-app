<script setup lang="ts">
import { ref, computed, watch, onUnmounted, nextTick } from 'vue';
import axios from 'axios';
import { AUDIO_SERVER_URL, BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from '../../../config';

const props = defineProps<{
  book: any;
  audioChapters: any[];
  userId: number;
  mode: string;
  isHost?: boolean;
  remoteCommand?: any;
}>();

const emit = defineEmits(['status-change', 'progress-change', 'player-control']);

const currentChapterIndex = ref(0);
const audioPlayer = ref<HTMLAudioElement | null>(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);
const calculatedPage = ref(0);
let progressUpdateTimeout: any = null;

const timeLeft = ref(25 * 60);
const isRunning = ref(false);
const currentMode = ref<'focus' | 'break'>('focus');
const sessionMinutes = ref(25);
let timerInterval: any = null;

const isAudioBook = computed(() => props.audioChapters && props.audioChapters.length > 0);

const currentAudioSrc = computed(() => {
  if (!props.audioChapters.length) return "";
  return `${AUDIO_SERVER_URL}/${props.audioChapters[currentChapterIndex.value].file_url}`;
});

const sounds = [
  { id: 'rain', name: 'Mưa rơi 🌧️', file: '/sounds/rain.mp3', color: 'from-gray-800 to-blue-900' },
  { id: 'cafe', name: 'White Noise ⚪', file: '/sounds/whitenoise.mp3', color: 'from-gray-500 to-slate-700' },
  { id: 'fireplace', name: 'Brown Noise 🟤', file: '/sounds/brownnoise.mp3', color: 'from-stone-800 to-stone-900' },
  { id: 'off', name: 'Yên lặng 🔇', file: '', color: 'from-gray-900 to-black' }
];
const currentSoundId = ref('off');
// Biến âm lượng (Mặc định 50%)
const volume = ref(0.5);
const currentSoundObj = computed(() => sounds.find(s => s.id === currentSoundId.value) || sounds[3]);

// Hàm hỗ trợ phát nhạc an toàn (Xử lý Autoplay Policy)
const safePlay = async () => {
    if (!audioPlayer.value) return;
    try {
        // Đảm bảo volume được set đúng trước khi play
        audioPlayer.value.volume = volume.value;
        await audioPlayer.value.play();
        isPlaying.value = true;
    } catch (error) {
        console.error("Autoplay bị chặn bởi trình duyệt:", error);
        // Nếu bị chặn, revert trạng thái UI về Pause để user biết bấm lại
        isPlaying.value = false;
        // Có thể thêm logic hiển thị thông báo "Vui lòng click vào trang để nghe" tại đây
    }
};

function playPause(fromSync = false) {
  if (!audioPlayer.value) return;

  if (props.mode === 'group' && !props.isHost && !fromSync) return;

  if (isPlaying.value) {
      audioPlayer.value.pause();
      // Nếu là click thủ công (Host hoặc Solo), cập nhật UI ngay
      isPlaying.value = false; 
      
      if (props.mode === 'group' && props.isHost && !fromSync) {
          emit('player-control', 'pause', { time: audioPlayer.value.currentTime });
          emit('status-change', 'paused');
      }
  } else {
      safePlay(); // Dùng hàm safePlay thay vì play trực tiếp
      
      if (props.mode === 'group' && props.isHost && !fromSync) {
          emit('player-control', 'play', { time: audioPlayer.value.currentTime });
          emit('status-change', 'listening');
      }
  }
}

function selectChapter(index: number, fromSync = false) {
  if (props.mode === 'group' && !props.isHost && !fromSync) return;

  if (index < 0 || index >= props.audioChapters.length) return;
  currentChapterIndex.value = index;
  nextTick(() => {
    if (audioPlayer.value) {
      audioPlayer.value.load();
      safePlay(); // Dùng safePlay
      
      // Đảm bảo âm lượng được set đúng khi chuyển bài
      audioPlayer.value.volume = volume.value;
      
      if (props.mode === 'group' && props.isHost && !fromSync) {
          emit('player-control', 'change_chapter', { index });
      }
    }
  });
}

function seekAudio(event: Event) {
  const target = event.target as HTMLInputElement;
  const time = Number(target.value);

  if (props.mode === 'group' && !props.isHost) return;

  if (audioPlayer.value && target) {
    audioPlayer.value.currentTime = time;
    
    if (props.mode === 'group' && props.isHost) {
        emit('player-control', 'seek', { time });
    }
  }
}

// Watch lệnh từ Host
watch(() => props.remoteCommand, (cmd) => {
    if (!cmd || !audioPlayer.value) return;
    if (props.isHost) return;

    switch (cmd.action) {
        case 'play':
            // Đồng bộ thời gian nếu lệch quá 0.5s (giảm ngưỡng xuống để chính xác hơn)
            if (Math.abs(audioPlayer.value.currentTime - cmd.payload.time) > 0.5) {
                audioPlayer.value.currentTime = cmd.payload.time;
            }
            safePlay(); // Dùng safePlay để bắt lỗi Autoplay
            break;
        case 'pause':
            audioPlayer.value.pause();
            isPlaying.value = false;
            // Đồng bộ lại thời gian khi pause để đảm bảo mọi người dừng cùng điểm
            if (cmd.payload.time) {
                audioPlayer.value.currentTime = cmd.payload.time;
                currentTime.value = cmd.payload.time;
            }
            break;
        case 'seek':
            audioPlayer.value.currentTime = cmd.payload.time;
            currentTime.value = cmd.payload.time;
            break;
        case 'change_chapter':
            selectChapter(cmd.payload.index, true);
            break;
    }
});

function onAudioEnded() {
  if (currentChapterIndex.value < props.audioChapters.length - 1) {
    if (props.mode !== 'group' || props.isHost) {
        selectChapter(currentChapterIndex.value + 1);
    }
  } else {
    isPlaying.value = false;
    if (props.book) scheduleProgressUpdate(props.book.page_count);
  }
}

function onTimeUpdate() {
  if (!audioPlayer.value || !props.book || !props.book.page_count) return;
  currentTime.value = audioPlayer.value.currentTime;
  duration.value = audioPlayer.value.duration;

  if (duration.value > 0) {
    const totalChapters = props.audioChapters.length;
    const percentOfCurrentChapter = currentTime.value / duration.value;
    const totalProgressPercent = (currentChapterIndex.value + percentOfCurrentChapter) / totalChapters;
    const newPage = Math.round(totalProgressPercent * props.book.page_count);

    if (newPage !== calculatedPage.value) {
      calculatedPage.value = newPage;
      emit('progress-change', newPage); 
      scheduleProgressUpdate(newPage);
    }
  }
}

function scheduleProgressUpdate(page: number) {
  if (progressUpdateTimeout) clearTimeout(progressUpdateTimeout);
  progressUpdateTimeout = setTimeout(async () => {
    try {
      await axios.put(
        `${BOOK_SERVICE_URL}books/reading-progress/${props.userId}/${props.book.id}`,
        null,
        { params: { current_page_from_user: page } }
      );
    } catch (e) {
      console.error(e);
    }
  }, 10000);
}

const formatTime = (seconds: number) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};
const formatTimeAudio = (s: number) => {
  if (isNaN(s)) return "00:00";
  const min = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${min}:${sec < 10 ? '0' + sec : sec}`;
}

watch(sessionMinutes, (newVal) => {
  if (!isRunning.value) timeLeft.value = newVal * 60;
});

function toggleTimer() {
  if (isRunning.value) {
    clearInterval(timerInterval);
    isRunning.value = false;
    emit('status-change', 'paused');
    if (audioPlayer.value) audioPlayer.value.pause();
  } else {
    isRunning.value = true;
    emit('status-change', currentMode.value);
    if (audioPlayer.value && (currentSoundId.value !== 'off' || isAudioBook.value)) {
      audioPlayer.value.play().catch(()=>{});
    }
    timerInterval = setInterval(() => {
      if (timeLeft.value > 0) {
        timeLeft.value--;
      } else {
        clearInterval(timerInterval);
        isRunning.value = false;
        if (audioPlayer.value) audioPlayer.value.pause();
        if (currentMode.value === 'focus') {
          currentMode.value = 'break';
          timeLeft.value = 5 * 60;
        } else {
          currentMode.value = 'focus';
          timeLeft.value = 25 * 60;
        }
        emit('status-change', 'idle');
        alert("Hết phiên!");
      }
    }, 1000);
  }
}

function resetTimer() {
    clearInterval(timerInterval);
    isRunning.value = false;
    timeLeft.value = sessionMinutes.value * 60;
    if (audioPlayer.value) audioPlayer.value.pause();
    emit('status-change', 'idle');
}

function changeSound(id: string) {
  currentSoundId.value = id;
  if (!audioPlayer.value) return;
  const sound = sounds.find(s => s.id === id);
  if (sound && sound.file) {
    audioPlayer.value.src = sound.file;
    audioPlayer.value.volume = volume.value;
    if (isRunning.value) audioPlayer.value.play().catch(()=>{});
  } else {
    audioPlayer.value.pause();
    audioPlayer.value.src = "";
  }
}

// Watch volume để cập nhật thẻ Audio thực tế
watch(volume, (newVol) => { 
    if (audioPlayer.value) audioPlayer.value.volume = newVol; 
});

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval);
});
</script>

<template>
    <div v-if="isAudioBook" class="flex-1 bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-2xl p-6 text-white flex flex-col overflow-hidden">
        <div class="flex gap-6 items-start mb-6">
            <div class="relative flex-shrink-0">
                <img v-if="book?.cover_url" :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" class="w-28 h-40 object-cover rounded-lg shadow-lg border border-white/10" :class="isPlaying ? 'animate-pulse' : ''" />
                <div v-else class="w-28 h-40 bg-white/10 rounded flex items-center justify-center text-2xl">📚</div>
            </div>
            <div class="flex-1 min-w-0">
                <h2 class="text-xl font-bold mb-1 truncate">{{ book?.title }}</h2>
                <p class="text-sm text-white/70 mb-3">{{ book?.author }}</p>
                <div class="bg-white/10 rounded-lg p-3 backdrop-blur-sm border border-white/5">
                    <p class="text-xs text-gray-400 uppercase tracking-wider mb-1">Đang phát</p>
                    <p class="text-sm font-semibold text-green-400 truncate">{{ audioChapters[currentChapterIndex]?.title || 'Đang tải...' }}</p>
                </div>
            </div>
        </div>
        <div class="flex-1 bg-black/20 rounded-lg border border-white/5 overflow-hidden flex flex-col mb-4">
            <div class="p-3 border-b border-white/10 text-xs font-bold text-gray-400 uppercase">Danh sách chương</div>
            <div class="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
                <div v-for="(chapter, idx) in audioChapters" :key="chapter.id" 
                    @click="selectChapter(idx)"
                    class="p-3 rounded flex items-center gap-3 transition-colors group"
                    :class="[
                        idx === currentChapterIndex ? 'bg-green-500/20 border border-green-500/30' : 'hover:bg-white/5 border border-transparent',
                        mode === 'group' && !isHost ? 'cursor-not-allowed opacity-70' : 'cursor-pointer'
                    ]">
                    <div class="text-xs font-mono w-6 text-right" :class="idx === currentChapterIndex ? 'text-green-400' : 'text-gray-500'">{{ idx + 1 }}</div>
                    <div class="flex-1 text-sm truncate" :class="idx === currentChapterIndex ? 'text-white font-medium' : 'text-gray-300 group-hover:text-white'">{{ chapter.title }}</div>
                    <div v-if="idx === currentChapterIndex" class="text-green-400 text-xs animate-pulse">🎵</div>
                </div>
            </div>
        </div>
        <div class="mt-auto">
            <div class="flex justify-between text-xs text-gray-400 mb-2"><span>{{ formatTimeAudio(currentTime) }}</span><span>{{ formatTimeAudio(duration) }}</span></div>
            <input 
                type="range" min="0" :max="duration" 
                v-model="currentTime" 
                @input="seekAudio"
                :disabled="mode === 'group' && !isHost"
                class="w-full h-1.5 bg-gray-700 rounded-lg appearance-none accent-green-500 mb-6 hover:h-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                :class="mode === 'group' && !isHost ? '' : 'cursor-pointer'"
            >
            <div class="flex justify-center items-center gap-8 mb-6">
                <button 
                    @click="selectChapter(Math.max(0, currentChapterIndex - 1))" 
                    :disabled="currentChapterIndex === 0 || (mode === 'group' && !isHost)" 
                    class="text-2xl text-gray-400 hover:text-white disabled:opacity-30 transition">
                    ⏮
                </button>
                
                <button 
                    @click="playPause(false)" 
                    class="w-14 h-14 bg-white text-black rounded-full flex items-center justify-center text-2xl hover:scale-110 hover:bg-green-400 transition shadow-lg shadow-green-900/20 disabled:bg-gray-400 disabled:cursor-not-allowed disabled:hover:scale-100"
                    :disabled="mode === 'group' && !isHost"
                >
                    {{ isPlaying ? '⏸' : '▶' }}
                </button>
                
                <button 
                    @click="selectChapter(Math.min(audioChapters.length - 1, currentChapterIndex + 1))" 
                    :disabled="currentChapterIndex === audioChapters.length - 1 || (mode === 'group' && !isHost)" 
                    class="text-2xl text-gray-400 hover:text-white disabled:opacity-30 transition">
                    ⏭
                </button>
            </div>

            <!-- THANH ĐIỀU CHỈNH ÂM LƯỢNG MỚI -->
            <div class="flex items-center justify-center gap-3 px-4 py-2 bg-black/20 rounded-full w-fit mx-auto backdrop-blur-sm mb-4">
                <button @click="volume = volume > 0 ? 0 : 0.5" class="text-gray-400 hover:text-white transition">
                    {{ volume === 0 ? '🔇' : volume < 0.5 ? '🔉' : '🔊' }}
                </button>
                <input 
                    type="range" min="0" max="1" step="0.05" 
                    v-model="volume"
                    class="w-24 h-1.5 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-green-400 hover:accent-green-300 transition-all"
                >
            </div>
            
            <div v-if="mode === 'group'" class="text-center">
                <span v-if="isHost" class="text-xs text-green-400 font-bold border border-green-500/30 px-2 py-1 rounded bg-green-500/10">👑 Bạn là Host - Đang điều khiển</span>
                <span v-else class="text-xs text-gray-400 font-medium italic">🎧 Đang đồng bộ theo Host...</span>
            </div>
            <div v-else class="text-center"><span v-if="calculatedPage > 0" class="text-xs text-green-300/80 font-mono">Tiến độ tự động: Trang {{ calculatedPage }}</span></div>
        </div>
        
        <audio 
            ref="audioPlayer" 
            :src="currentAudioSrc" 
            @timeupdate="onTimeUpdate" 
            @ended="onAudioEnded" 
            @play="isPlaying = true" 
            @pause="isPlaying = false" 
            hidden
        ></audio>
    </div>

    <div v-else class="flex-1 rounded-2xl shadow-2xl border p-6 text-white flex flex-col relative transition-colors duration-1000" :class="['bg-gradient-to-br', currentSoundObj.color]">
        <div class="absolute top-4 right-4 z-20">
            <div class="flex items-center gap-2 bg-black/30 px-3 py-1 rounded-full backdrop-blur-md border border-white/10">
                <span class="text-xs">🎵</span>
                <select v-model="currentSoundId" @change="changeSound(currentSoundId)" class="bg-transparent text-xs outline-none cursor-pointer">
                    <option v-for="s in sounds" :key="s.id" :value="s.id" class="text-black">{{ s.name }}</option>
                </select>
            </div>
        </div>
        <div class="flex-1 flex flex-col items-center justify-center">
            <h2 class="text-white/80 font-bold tracking-widest mb-6">POMODORO TIMER</h2>
            <div class="text-9xl font-mono font-bold text-white mb-8">{{ formatTime(timeLeft) }}</div>
            <div class="flex gap-4">
                <button @click="toggleTimer" class="px-10 py-4 bg-white text-gray-900 rounded-full font-bold text-lg hover:bg-gray-100 transition shadow-lg">{{ isRunning ? 'Tạm dừng' : 'Bắt đầu đọc' }}</button>
                <button @click="resetTimer" class="px-4 py-4 bg-white/10 text-white rounded-full font-bold hover:bg-white/20">↺</button>
            </div>
            <p class="mt-6 text-white/60 text-sm italic">{{ isRunning ? 'Đang trong phiên đọc...' : 'Sẵn sàng để bắt đầu' }}</p>
            <audio ref="audioPlayer" loop hidden></audio>
        </div>
    </div>
</template>