<script setup lang="ts">
import { ref, nextTick, onMounted } from 'vue';
import axios from 'axios';
import { BOOK_SERVICE_URL } from '../../config';

const props = defineProps<{
  bookId: number,
  bookTitle: string
}>();

const emit = defineEmits(['close']);

interface Message {
  sender: 'user' | 'ai';
  text: string;
}

const characterName = ref("");
const isCharacterSet = ref(false); 
const messages = ref<Message[]>([]);
const userInput = ref("");
const isLoading = ref(false);
const chatBoxRef = ref<HTMLElement | null>(null);

const suggestedCharacters = ref<string[]>([]);
const loadingSuggestions = ref(false);

function setCharacter(name: string) {
  characterName.value = name;
  isCharacterSet.value = true;
  
  messages.value.push({
    sender: 'ai',
    text: `Chào bạn, tôi là ${characterName.value}. Bạn muốn hỏi gì về câu chuyện của tôi?`
  });
}

async function sendMessage() {
  if (!userInput.value.trim() || isLoading.value) return;

  const text = userInput.value;
  
  const historyToSend = messages.value.slice(-10).map(msg => ({
    role: msg.sender === 'user' ? 'user' : 'model',
    message: msg.text
  }));

  messages.value.push({ sender: 'user', text: text });
  userInput.value = "";
  scrollToBottom();

  isLoading.value = true;
  try {
    const res = await axios.post(`${BOOK_SERVICE_URL}ai/recommendations/chat-character`, {
      book_id: props.bookId,
      character_name: characterName.value,
      user_message: text,
      history: historyToSend
    });

    messages.value.push({ sender: 'ai', text: res.data.reply });
    scrollToBottom();

  } catch (err) {
    messages.value.push({ sender: 'ai', text: "Hmm... tôi đang hơi mất tập trung (Lỗi kết nối)." });
  } finally {
    isLoading.value = false;
    scrollToBottom(); 
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatBoxRef.value) {
      chatBoxRef.value.scrollTop = chatBoxRef.value.scrollHeight;
    }
  });
}

function resetChat() {
    isCharacterSet.value = false;
    messages.value = [];
    characterName.value = "";
}

async function loadCharacters() {
    loadingSuggestions.value = true;
    try {
        const res = await axios.get(`${BOOK_SERVICE_URL}ai/recommendations/characters/${props.bookId}`);
        suggestedCharacters.value = res.data.characters;
    } catch (e) {
        console.error(e);
    } finally {
        loadingSuggestions.value = false;
    }
}

onMounted(() => {
    loadCharacters();
});
</script>

<template>
  <!-- Điều chỉnh chiều cao cố định h-[500px] để đủ không gian cho chat -->
  <div class="fixed bottom-24 right-6 z-50 w-80 md:w-96 h-[500px] flex flex-col bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden transition-all duration-300 ease-in-out transform origin-bottom-right ring-1 ring-black/5">
      
      <!-- Header Gradient đẹp mắt -->
      <div class="bg-gradient-to-r from-violet-600 to-indigo-600 p-3 flex justify-between items-center text-white shadow-md shrink-0">
        <div class="flex items-center gap-2.5">
            <div class="bg-white/20 p-1.5 rounded-lg backdrop-blur-sm">
                <span class="text-lg">🤖</span>
            </div>
            <div>
                <h3 class="font-bold text-sm tracking-wide">Chat với Nhân vật</h3>
                <p class="text-[10px] opacity-90 truncate max-w-[180px] font-medium">{{ props.bookTitle }}</p>
            </div>
        </div>
        <button @click="$emit('close')" class="text-white/80 hover:text-white hover:bg-white/20 rounded-full p-1.5 transition">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-5 h-5">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
        </button>
      </div>

      <!-- Màn hình 1: Chọn Nhân vật (Đã bỏ ô nhập) -->
      <div v-if="!isCharacterSet" class="flex flex-col h-full bg-gray-50 overflow-hidden">
        
        <!-- Hero Section nhỏ -->
        <div class="p-6 text-center bg-white border-b border-gray-100 shrink-0">
            <div class="text-4xl mb-3 animate-bounce">👋</div>
            <h4 class="font-bold text-gray-800 text-base">Chào bạn!</h4>
            <p class="text-gray-500 text-xs mt-1">Chọn một nhân vật để bắt đầu trò chuyện.</p>
        </div>

        <!-- Danh sách nhân vật (Cuộn được) -->
        <div class="flex-1 overflow-y-auto p-4 space-y-2 custom-scrollbar">
            <div v-if="loadingSuggestions" class="flex flex-col items-center justify-center py-8 space-y-3">
                <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-violet-600"></div>
                <span class="text-xs text-gray-400">Đang triệu hồi nhân vật...</span>
            </div>

            <template v-else>
                <button 
                    v-for="char in suggestedCharacters" 
                    :key="char"
                    @click="setCharacter(char)"
                    class="w-full text-left px-4 py-3 bg-white border border-gray-200 rounded-xl hover:border-violet-400 hover:shadow-md hover:bg-violet-50 transition-all duration-200 group flex items-center justify-between"
                >
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 rounded-full bg-violet-100 text-violet-600 flex items-center justify-center text-xs font-bold">
                            {{ char.charAt(0).toUpperCase() }}
                        </div>
                        <span class="font-medium text-sm text-gray-700 group-hover:text-violet-700">{{ char }}</span>
                    </div>
                    <span class="text-gray-300 group-hover:text-violet-500 text-lg">&rsaquo;</span>
                </button>

                <div v-if="suggestedCharacters.length === 0" class="text-center text-gray-400 text-xs py-4">
                    Không tìm thấy nhân vật nào.
                </div>
            </template>
        </div>
      </div>

      <!-- Màn hình 2: Khung Chat (Giữ nguyên logic, tinh chỉnh CSS) -->
      <div v-else class="flex flex-col flex-1 overflow-hidden bg-gray-50">
        
        <!-- Thanh tên nhân vật -->
        <div class="bg-white px-4 py-2.5 flex justify-between items-center border-b shadow-sm z-10 shrink-0">
            <div class="flex items-center gap-2">
                <div class="relative">
                    <div class="w-2 h-2 rounded-full bg-green-500"></div>
                    <div class="w-2 h-2 rounded-full bg-green-500 absolute top-0 left-0 animate-ping opacity-75"></div>
                </div>
                <span class="font-bold text-xs text-gray-700 truncate max-w-[150px]">{{ characterName }}</span>
            </div>
            <button @click="resetChat" class="text-[10px] font-medium text-gray-400 hover:text-red-500 hover:bg-red-50 px-2 py-1 rounded transition">
                Kết thúc
            </button>
        </div>

        <!-- Nội dung tin nhắn -->
        <div ref="chatBoxRef" class="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
            <div 
                v-for="(msg, index) in messages" 
                :key="index"
                class="flex w-full"
                :class="msg.sender === 'user' ? 'justify-end' : 'justify-start'"
            >
                <div 
                    class="max-w-[85%] rounded-2xl px-3.5 py-2 text-xs shadow-sm leading-relaxed break-words"
                    :class="msg.sender === 'user' 
                        ? 'bg-violet-600 text-white rounded-br-none' 
                        : 'bg-white text-gray-800 border border-gray-200 rounded-bl-none'"
                >
                    {{ msg.text }}
                </div>
            </div>
            
            <div v-if="isLoading" class="flex justify-start w-full">
                <div class="bg-gray-200/50 text-gray-500 rounded-2xl px-3 py-2 text-[10px] italic flex gap-1 items-center">
                    <span class="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></span>
                    <span class="w-1 h-1 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                    <span class="w-1 h-1 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                </div>
            </div>
        </div>

        <!-- Input chat -->
        <div class="p-3 bg-white border-t flex gap-2 items-center shrink-0">
            <input 
                v-model="userInput"
                @keydown.enter="sendMessage"
                type="text" 
                class="flex-1 bg-gray-50 border border-gray-200 focus:bg-white focus:border-violet-500 rounded-full px-4 py-2 text-xs focus:outline-none transition placeholder-gray-400"
                placeholder="Nhập tin nhắn..."
            />
            <button 
                @click="sendMessage"
                :disabled="isLoading || !userInput.trim()"
                class="bg-violet-600 text-white p-2 rounded-full hover:bg-violet-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition transform active:scale-95"
            >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-4 h-4">
                    <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                </svg>
            </button>
        </div>
      </div>

  </div>
</template>

<style scoped>
/* Tùy chỉnh thanh cuộn cho gọn */
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e5e7eb;
  border-radius: 20px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background-color: #d1d5db;
}
</style>