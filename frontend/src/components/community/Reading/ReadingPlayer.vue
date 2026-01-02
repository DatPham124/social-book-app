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

const emit = defineEmits(['status-change', 'progress-change', 'player-control', 'send-reaction']);

const reactions = ['❤️', '😂', '😮', '😢', '🔥', '👏'];

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
const volume = ref(0.5);
const currentSoundObj = computed(() => sounds.find(s => s.id === currentSoundId.value) || sounds[3]);

function emitReaction(emoji: string) {
  emit('send-reaction', emoji);
}

const safePlay = async () => {
  if (!audioPlayer.value) return;
  try {
    audioPlayer.value.volume = volume.value;
    await audioPlayer.value.play();
    isPlaying.value = true;
  } catch (error) {
    console.error("Autoplay bị chặn:", error);
    isPlaying.value = false;
  }
};

function playPause(fromSync = false) {
  if (!audioPlayer.value) return;

  if (props.mode === 'group' && !props.isHost && !fromSync) return;

  if (isPlaying.value) {
    audioPlayer.value.pause();
    isPlaying.value = false;

    if (props.mode === 'group' && props.isHost && !fromSync) {
      emit('player-control', 'pause', { time: audioPlayer.value.currentTime });
      emit('status-change', 'paused');
    }
  } else {
    safePlay();
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
      safePlay();
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

watch(() => props.remoteCommand, (cmd) => {
  if (!cmd || !audioPlayer.value) return;
  if (props.isHost) return;

  switch (cmd.action) {
    case 'play':
      if (Math.abs(audioPlayer.value.currentTime - cmd.payload.time) > 0.5) {
        audioPlayer.value.currentTime = cmd.payload.time;
      }
      safePlay();
      break;
    case 'pause':
      audioPlayer.value.pause();
      isPlaying.value = false;
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
      audioPlayer.value.play().catch(() => { });
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
    if (isRunning.value) audioPlayer.value.play().catch(() => { });
  } else {
    audioPlayer.value.pause();
    audioPlayer.value.src = "";
  }
}

watch(volume, (newVol) => {
  if (audioPlayer.value) audioPlayer.value.volume = newVol;
});

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval);
});
</script>

<template>
  <div v-if="isAudioBook"
    class="flex-1 bg-gray-900 text-white rounded-3xl shadow-2xl p-8 flex flex-col overflow-hidden relative border border-gray-800">
    <!-- Background Blur Effect -->
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none z-0">
      <div class="absolute top-[-10%] right-[-10%] w-64 h-64 bg-green-500/20 rounded-full blur-[100px]"></div>
      <div class="absolute bottom-[-10%] left-[-10%] w-64 h-64 bg-blue-500/20 rounded-full blur-[100px]"></div>
    </div>

    <div class="relative z-10 flex flex-col h-full">
      <!-- HEADER: Cover + Info -->
      <div class="flex gap-6 items-center mb-8">
        <div class="relative flex-shrink-0 group">
          <img v-if="book?.cover_url" :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`"
            class="w-24 h-36 object-cover rounded-xl shadow-lg group-hover:scale-105 transition-transform duration-500 ease-out"
            :class="isPlaying ? 'shadow-green-500/20' : ''" />
          <div v-else class="w-24 h-36 bg-gray-800 rounded-xl flex items-center justify-center text-2xl">📚</div>
        </div>
        <div class="flex-1 min-w-0">
          <h2 class="text-2xl font-bold mb-1 truncate tracking-tight">{{ book?.title }}</h2>
          <p class="text-sm text-gray-400 mb-3">{{ book?.author }}</p>
          <div
            class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 backdrop-blur-md">
            <span class="w-1.5 h-1.5 rounded-full"
              :class="isPlaying ? 'bg-green-400 animate-pulse' : 'bg-gray-500'"></span>
            <span class="text-xs font-medium text-gray-300 truncate max-w-[150px]">
              {{ audioChapters[currentChapterIndex]?.title || 'Đang tải...' }}
            </span>
          </div>
        </div>
      </div>

      <!-- CHAPTER LIST (Gọn gàng hơn) -->
      <div class="flex-1 bg-black/20 rounded-2xl border border-white/5 overflow-hidden flex flex-col mb-6">
        <div class="p-4 border-b border-white/5 bg-white/5 backdrop-blur-sm flex justify-between items-center">
          <span class="text-xs font-bold text-gray-400 uppercase tracking-widest">Danh sách chương</span>
          <span class="text-xs text-gray-500">{{ audioChapters.length }} chương</span>
        </div>
        <div class="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
          <div v-for="(chapter, idx) in audioChapters" :key="chapter.id" @click="selectChapter(idx)"
            class="p-3 rounded-xl flex items-center gap-3 transition-all duration-200 group cursor-pointer" :class="[
              idx === currentChapterIndex ? 'bg-white/10 border border-white/10' : 'hover:bg-white/5 border border-transparent',
              mode === 'group' && !isHost ? 'opacity-70' : ''
            ]">
            <span class="text-xs font-mono w-6 text-center opacity-50"
              :class="idx === currentChapterIndex ? 'text-green-400 opacity-100' : ''">{{ idx + 1 }}</span>
            <span class="flex-1 text-sm truncate font-medium"
              :class="idx === currentChapterIndex ? 'text-white' : 'text-gray-400 group-hover:text-gray-200'">{{
              chapter.title }}</span>
            <span v-if="idx === currentChapterIndex" class="text-green-400 text-xs">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                  clip-rule="evenodd" />
              </svg>
            </span>
          </div>
        </div>
      </div>

      <!-- CONTROLS SECTION -->
      <div class="mt-auto">
        <!-- Progress Bar -->
        <div class="group mb-6">
          <div class="flex justify-between text-xs text-gray-500 mb-2 font-mono tracking-wider">
            <span>{{ formatTimeAudio(currentTime) }}</span>
            <span>{{ formatTimeAudio(duration) }}</span>
          </div>
          <input type="range" min="0" :max="duration" v-model="currentTime" @input="seekAudio"
            :disabled="mode === 'group' && !isHost"
            class="w-full h-1.5 bg-gray-700 rounded-full appearance-none cursor-pointer accent-white hover:accent-green-400 transition-colors focus:outline-none disabled:cursor-not-allowed disabled:accent-gray-500"
            :style="`background: linear-gradient(to right, ${mode === 'group' && !isHost ? '#6b7280' : '#10b981'} ${(currentTime / duration) * 100}%, #374151 ${(currentTime / duration) * 100}%)`">
        </div>

        <!-- Main Controls (Minimalist) -->
        <div class="flex justify-center items-center gap-10 mb-8">
          <!-- PREV -->
          <button @click="selectChapter(Math.max(0, currentChapterIndex - 1))"
            :disabled="currentChapterIndex === 0 || (mode === 'group' && !isHost)"
            class="text-gray-500 hover:text-white disabled:opacity-30 transition-colors p-2 rounded-full hover:bg-white/5 active:scale-95">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>

          <!-- PLAY/PAUSE (Centerpiece) -->
          <button @click="playPause(false)" >
            <!-- Icon Play (Thêm ml-1 để căn giữa hình tam giác) -->
            <svg v-if="!isPlaying" xmlns="http://www.w3.org/2000/svg" class="h-12 w-12" viewBox="0 0 20 20"
              fill="currentColor">
              <path fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                clip-rule="evenodd" />
            </svg>
            <!-- Icon Pause -->
            <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-12 w-12" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                clip-rule="evenodd" />
            </svg>
          </button>

          <!-- NEXT -->
          <button @click="selectChapter(Math.min(audioChapters.length - 1, currentChapterIndex + 1))"
            :disabled="currentChapterIndex === audioChapters.length - 1 || (mode === 'group' && !isHost)"
            class="text-gray-500 hover:text-white disabled:opacity-30 transition-colors p-2 rounded-full hover:bg-white/5 active:scale-95">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 5l7 7-7 7M5 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <!-- Volume & Reactions Row -->
        <div class="flex flex-col md:flex-row justify-between items-center gap-4">
          <!-- Reactions -->
          <div v-if="mode === 'group'" class="flex gap-3">
            <button v-for="emoji in reactions" :key="emoji" @click="emitReaction(emoji)"
              class="text-lg hover:scale-125 transition transform active:scale-95 bg-white/5 w-10 h-10 rounded-full flex items-center justify-center hover:bg-white/10 border border-white/5">
              {{ emoji }}
            </button>
          </div>

          <!-- Volume Slider (Minimal) -->
          <div
            class="flex items-center gap-3 bg-black/20 px-4 py-2 rounded-full border border-white/5 backdrop-blur-sm">
            <button @click="volume = volume > 0 ? 0 : 0.5" class="text-gray-400 hover:text-white transition">
              <svg v-if="volume === 0" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20"
                fill="currentColor">
                <path fill-rule="evenodd"
                  d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM12.293 7.293a1 1 0 011.414 0L15 8.586l1.293-1.293a1 1 0 111.414 1.414L16.414 10l1.293 1.293a1 1 0 01-1.414 1.414L15 11.414l-1.293 1.293a1 1 0 01-1.414-1.414L13.586 10l-1.293-1.293a1 1 0 010-1.414z"
                  clip-rule="evenodd" />
              </svg>
              <svg v-else-if="volume < 0.5" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20"
                fill="currentColor">
                <path fill-rule="evenodd"
                  d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217z"
                  clip-rule="evenodd" />
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd"
                  d="M9.383 3.076A1 1 0 0110 4v12a1 1 0 01-1.707.707L4.586 13H2a1 1 0 01-1-1V8a1 1 0 011-1h2.586l3.707-3.707a1 1 0 011.09-.217zM14.657 2.929a1 1 0 011.414 0A9.972 9.972 0 0119 10a9.972 9.972 0 01-2.929 7.071 1 1 0 01-1.414-1.414A7.971 7.971 0 0017 10c0-2.21-.894-4.208-2.343-5.657a1 1 0 010-1.414zm-2.829 2.828a1 1 0 011.415 0A5.983 5.983 0 0115 10a5.984 5.984 0 01-1.757 4.243 1 1 0 01-1.415-1.415A3.984 3.984 0 0013 10a3.983 3.983 0 00-1.172-2.828 1 1 0 010-1.415z"
                  clip-rule="evenodd" />
              </svg>
            </button>
            <input type="range" min="0" max="1" step="0.05" v-model="volume"
              class="w-20 h-1 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-white hover:accent-gray-300 transition-all">
          </div>
        </div>

        <!-- Status -->
        <div v-if="mode === 'group'" class="text-center mt-6">
          <span v-if="isHost"
            class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-green-500/30 bg-green-500/10 text-green-400 text-[10px] font-bold uppercase tracking-wider">
            <span class="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span> Host Control
          </span>
          <span v-else
            class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-gray-500/30 bg-gray-500/10 text-gray-400 text-[10px] font-bold uppercase tracking-wider">
            <span class="w-1.5 h-1.5 rounded-full bg-gray-400"></span> Listener
          </span>
        </div>
      </div>
    </div>

    <audio ref="audioPlayer" :src="currentAudioSrc" @timeupdate="onTimeUpdate" @ended="onAudioEnded"
      @play="isPlaying = true" @pause="isPlaying = false" hidden></audio>
  </div>

  <div v-else
    class="flex-1 rounded-2xl shadow-2xl border p-6 text-white flex flex-col relative transition-colors duration-1000"
    :class="['bg-gradient-to-br', currentSoundObj.color]">
    <div class="absolute top-4 right-4 z-20">
      <div class="flex items-center gap-2 bg-black/30 px-3 py-1 rounded-full backdrop-blur-md border border-white/10">
        <span class="text-xs">🎵</span>
        <select v-model="currentSoundId" @change="changeSound(currentSoundId)"
          class="bg-transparent text-xs outline-none cursor-pointer">
          <option v-for="s in sounds" :key="s.id" :value="s.id" class="text-black">{{ s.name }}</option>
        </select>
      </div>
    </div>
    <div class="flex-1 flex flex-col items-center justify-center">
      <h2 class="text-white/80 font-bold tracking-widest mb-6">POMODORO TIMER</h2>
      <div class="text-9xl font-mono font-bold text-white mb-8">{{ formatTime(timeLeft) }}</div>
      <div class="flex gap-4">
        <button @click="toggleTimer"
          class="px-10 py-4 bg-white text-gray-900 rounded-full font-bold text-lg hover:bg-gray-100 transition shadow-lg">{{
            isRunning ? 'Tạm dừng' : 'Bắt đầu đọc' }}</button>
        <button @click="resetTimer"
          class="px-4 py-4 bg-white/10 text-white rounded-full font-bold hover:bg-white/20">↺</button>
      </div>
      <p class="mt-6 text-white/60 text-sm italic">{{ isRunning ? 'Đang trong phiên đọc...' : 'Sẵn sàng để bắt đầu' }}
      </p>
      <audio ref="audioPlayer" loop hidden></audio>
    </div>
  </div>
</template>