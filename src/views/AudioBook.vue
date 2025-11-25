<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue';
import Navbar from '../components/layout/Navbar.vue';
import ReadingPlayer from '../components/community/Reading/ReadingPlayer.vue';
import GroupChatPanel from '../components/community/Reading/GroupChatPanel.vue';
import { useAuth } from '../composables/useAuth';
import { useBooks } from '../composables/useBook';
import { BOOK_SERVICE_URL, USER_SERVICE_URL } from '../config';
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router';
import axios from 'axios';
import { useAudioSync } from '../composables/useAudioSync';

const props = withDefaults(defineProps<{
  mode?: 'group' | 'solo';
}>(), { mode: 'group' });

const route = useRoute();
const router = useRouter();
const { userInfo } = useAuth(); 

const { joinRoom, leaveRoom, sendControl, remoteCommand } = useAudioSync();

const currentBook = ref<any>(null);
const audioChapters = ref<any[]>([]);
const loading = ref(true);
const chatPanelRef = ref<any>(null); 
const showExitModal = ref(false);
const pendingNextRoute = ref<Function | null>(null);
const currentProgressPage = ref(0);
const hostId = ref<number | null>(null);

const roomId = computed(() => {
    if (props.mode === 'group') return `buddy_${route.params.id}`;
    return userInfo.value ? `solo_${userInfo.value.user_id}` : '';
});

const isHost = computed(() => {
    if (props.mode === 'solo') return true;
    if (!userInfo.value || hostId.value === null) return false;
    
    return String(userInfo.value.user_id) === String(hostId.value);
});

async function getProfile(userId: number) {
  try {
    const token = localStorage.getItem("token");
    const response = await axios.get(
      `${USER_SERVICE_URL}users/profile/${userId}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    return response.data; 
  } catch (error) {
    return null;
  }
}

async function loadBookInfo() {
    try {
        let targetBookId = 0;
        if (props.mode === 'group') {
             const brRes = await axios.get(`${BOOK_SERVICE_URL}buddyreads/${route.params.id}`);
             targetBookId = brRes.data.book_id;
             hostId.value = brRes.data.created_by_user_id; 
        } else {
             targetBookId = Number(route.params.id);
        }
        
        const res = await axios.get(`${BOOK_SERVICE_URL}books/${targetBookId}/details`);
        currentBook.value = res.data;
        audioChapters.value = (res.data.audios || []).sort((a: any, b: any) => a.order - b.order);

        if (props.mode === 'group' && userInfo.value) {
            joinRoom(roomId.value, userInfo.value.user_id);
        }

    } catch (error) { console.error(error); } finally { loading.value = false; }
}

function handleStatusChange(status: string) {
    if (props.mode === 'group' && chatPanelRef.value?.updateUserStatus) {
        chatPanelRef.value.updateUserStatus(status);
    }
}

function handlePlayerControl(action: string, payload: any) {
    if (props.mode === 'group') {
        if (isHost.value && userInfo.value) {
            sendControl(roomId.value, action, payload, userInfo.value.user_id);
        }
    }
}

function handleProgressChange(page: number) {
    currentProgressPage.value = page;
}

onBeforeRouteLeave((to, from, next) => {
  if (currentProgressPage.value > 0 && audioChapters.value.length > 0) {
      showExitModal.value = true;
      pendingNextRoute.value = next;
  } else {
      next();
  }
});

async function confirmExit(save: boolean) {
    if (save && currentBook.value && userInfo.value) {
        try {
            await axios.put(`${BOOK_SERVICE_URL}books/reading-progress/${userInfo.value.user_id}/${currentBook.value.id}`, null, { params: { current_page_from_user: currentProgressPage.value } });
        } catch(e) { console.error("Lỗi lưu:", e); }
    }
    if (props.mode === 'group') leaveRoom();
    showExitModal.value = false;
    if (pendingNextRoute.value) pendingNextRoute.value();
}

onMounted(async () => {
    if (!userInfo.value) {
        router.push('/login');
        return;
    }
    const detailedProfile = await getProfile(userInfo.value.user_id);
    if (detailedProfile) Object.assign(userInfo.value, detailedProfile);
    await loadBookInfo();
});

onUnmounted(() => {
    if (props.mode === 'group') leaveRoom();
});

function goBack() { router.back(); }
</script>

<template>
  <Navbar />
  <div class="max-w-7xl mx-auto p-4 md:p-6 h-[calc(100vh-80px)]">
    
    <div class="flex items-center justify-between mb-4">
        <button @click="goBack" class="text-gray-600 hover:text-yellow-600 font-medium flex items-center gap-2">
            &larr; {{ props.mode === 'group' ? 'Rời phòng nhóm' : 'Quay lại' }}
        </button>
        <div class="text-sm font-bold text-gray-700" v-if="currentBook">
             {{ audioChapters.length > 0 ? '🎧 PHÒNG NGHE' : '📖 PHÒNG ĐỌC' }} - {{ currentBook.title }}
        </div>
    </div>

    <div v-if="loading" class="text-center py-10">Đang tải...</div>

    <div v-else class="grid gap-6 h-full pb-10" 
         :class="props.mode === 'group' ? 'grid-cols-1 lg:grid-cols-3' : 'grid-cols-1 max-w-4xl mx-auto'">
        
        <div class="flex flex-col h-full" :class="props.mode === 'group' ? 'lg:col-span-2' : 'w-full'">
            <ReadingPlayer 
                v-if="currentBook && userInfo"
                :book="currentBook"
                :audioChapters="audioChapters"
                :userId="userInfo.user_id"
                :mode="props.mode"
                :isHost="isHost"
                :remoteCommand="remoteCommand"
                @player-control="handlePlayerControl"
                @status-change="handleStatusChange"
                @progress-change="handleProgressChange"
            />
        </div>

        <div v-if="props.mode === 'group'" class="h-full overflow-hidden">
            <GroupChatPanel 
                v-if="userInfo && roomId"
                ref="chatPanelRef"
                :roomId="roomId"
                :userInfo="userInfo"
            />
        </div>
    </div>

    <div v-if="showExitModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div class="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6">
            <h3 class="text-lg font-bold mb-2">Lưu tiến độ?</h3>
            <p class="text-sm text-gray-600 mb-4">Bạn đang ở trang {{ currentProgressPage }}.</p>
            <div class="flex flex-col gap-2">
                <button @click="confirmExit(true)" class="bg-green-600 text-white py-2 rounded font-bold hover:bg-green-700">Lưu & Thoát</button>
                <button @click="confirmExit(false)" class="bg-gray-200 text-gray-800 py-2 rounded hover:bg-gray-300">Không lưu</button>
                <button @click="showExitModal = false" class="text-gray-500 text-sm mt-1 hover:underline">Hủy</button>
            </div>
        </div>
    </div>
  </div>
</template>