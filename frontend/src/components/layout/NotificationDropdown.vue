<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useNotifications } from '../../composables/useNotifications';
import { AVATAR_SERVER_URL } from '../../config';
import { useRouter } from 'vue-router';

const { notifications, unreadCount, markAsRead, handleBuddyInvite, startPolling, stopPolling } = useNotifications();
const isOpen = ref(false);
const router = useRouter();

onMounted(() => startPolling());
onUnmounted(() => stopPolling());

function toggleDropdown() { isOpen.value = !isOpen.value; }

function timeAgo(timestamp: number) {
    const diff = Date.now() - timestamp;
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Vừa xong';
    if (mins < 60) return `${mins} phút trước`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours} giờ trước`;
    return new Date(timestamp).toLocaleDateString('vi-VN');
}

// SỬA HÀM CLICK
function handleClick(item: any) {
    if (item.category === 'normal') {
        if (item.status === 'unread') markAsRead(item);
        
        if (item.type === 'friend_request') {
            router.push('/friends');
        } 
        else if (item.type === 'buddy_chat') {
            if (item.room_id) router.push({ name: 'ImmersiveRead', params: { id: item.room_id.split('_')[1] } });
        }
        // Điều hướng CLB
        else if (item.room_id) {
            if (item.room_id.startsWith('meeting_')) {
                router.push(`/meeting/${item.room_id.split('_')[1]}`);
            }
            else if (item.room_id.startsWith('discussion_')) {
                router.push(`/discussion/${item.room_id.split('_')[1]}`);
            }
            else if (item.room_id.startsWith('club_members_')) {
                router.push(`/bookclub/${item.room_id.split('_')[2]}`);
            }
            else if (item.room_id.startsWith('club_')) {
                router.push(`/bookclub/${item.room_id.split('_')[1]}`);
            }
            else if (item.room_id.startsWith('book_')) {
                const bookId = item.room_id.split('_')[1];
                router.push(`/book/${bookId}`);
            }
        }
        
        isOpen.value = false;
    }
}
</script>

<template>
    <div class="relative">
        <!-- Nút chuông (Giữ nguyên) -->
        <button @click="toggleDropdown" class="relative p-2 text-gray-600 hover:text-yellow-600 transition rounded-full focus:outline-none hover:bg-gray-100">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
            </svg>
            <span v-if="unreadCount > 0" class="absolute top-0 right-0 bg-red-500 text-white text-[10px] font-bold px-1.5 py-0.5 rounded-full border-2 border-white animate-pulse shadow-sm">
                {{ unreadCount > 99 ? '99+' : unreadCount }}
            </span>
        </button>

        <!-- Dropdown (Cập nhật phần hiển thị nội dung) -->
        <div v-if="isOpen" class="absolute right-0 mt-3 w-80 md:w-96 bg-white rounded-xl shadow-2xl border border-gray-100 overflow-hidden z-50 origin-top-right ring-1 ring-black ring-opacity-5">
            <div class="p-3 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                <h3 class="font-bold text-gray-800 text-sm">Thông báo</h3>
                <router-link to="/notifications" class="text-xs text-yellow-600 hover:underline" @click="isOpen = false">Xem tất cả</router-link>
            </div>

            <div class="max-h-[400px] overflow-y-auto custom-scrollbar">
                <div v-if="notifications.length === 0" class="p-8 text-center text-gray-400 text-sm italic">
                    Bạn không có thông báo mới.
                </div>

                <div v-for="item in notifications" :key="`${item.type}-${item.id}`" 
                     class="p-4 border-b border-gray-50 hover:bg-gray-50 transition flex gap-3 relative group"
                     :class="{ 'bg-blue-50/40': (item.category === 'normal' && item.status === 'unread') || (item.category === 'invite' && item.status === 'pending') }"
                >
                    <!-- Avatar -->
                    <div class="flex-shrink-0 mt-1">
                        <div v-if="item.type === 'buddy_chat' && item.count > 1" class="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold border border-indigo-200">
                            {{ item.count }}
                        </div>
                        
                        <template v-else>
                            <img v-if="item.sender_info?.avatar_url" :src="`${AVATAR_SERVER_URL}/${item.sender_info.avatar_url}`" class="w-10 h-10 rounded-full object-cover border border-gray-200">
                            <div v-else class="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center text-yellow-700 font-bold text-xs border border-yellow-200">
                                {{ item.sender_info?.username?.charAt(0).toUpperCase() || 'U' }}
                            </div>
                        </template>
                    </div>

                    <!-- Content -->
                    <div class="flex-1 min-w-0">
                        <div @click="handleClick(item)" class="cursor-pointer">
                            <p class="text-sm text-gray-800 leading-snug truncate-2-lines">
                                <span class="font-bold">{{ item.sender_info?.username || 'Người dùng' }}</span> 
                                {{ item.display_message }}
                            </p>
                            <p class="text-xs text-gray-400 mt-1">{{ timeAgo(item.timestamp)}}</p>
                        </div>

                        <!-- Nút hành động cho Invite (Giữ nguyên) -->
                        <div v-if="item.type === 'buddy_read_invite' && item.status === 'pending'" class="mt-2 flex gap-2">
                            <button @click="handleBuddyInvite(item, 'accept')" class="px-3 py-1 bg-teal-600 text-white text-xs font-bold rounded hover:bg-teal-700 transition shadow-sm">Đọc cùng</button>
                            <button @click="handleBuddyInvite(item, 'decline')" class="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-bold rounded hover:bg-gray-200 transition">Từ chối</button>
                        </div>
                    </div>

                    <div v-if="item.category === 'normal' && item.status === 'unread'" class="self-center shrink-0">
                        <span class="block w-2.5 h-2.5 bg-blue-500 rounded-full shadow-sm"></span>
                    </div>
                </div>
            </div>
        </div>
        
        <div v-if="isOpen" @click="isOpen = false" class="fixed inset-0 z-40 cursor-default"></div>
    </div>
</template>

<style scoped>
.truncate-2-lines { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 10px; }
</style>