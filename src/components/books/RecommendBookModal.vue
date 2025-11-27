<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { USER_SERVICE_URL, AVATAR_SERVER_URL } from '../../config';
import { useAuth } from '../../composables/useAuth';
import { getProfile } from '../../composables/useProfile';

const props = defineProps<{
    bookId: number;
    bookTitle: string;
}>();

const emit = defineEmits(['close']);
const { userInfo } = useAuth();

const friends = ref<any[]>([]);
const selectedFriends = ref<number[]>([]);
const message = ref("");
const loading = ref(true);
const sending = ref(false);

// 1. Tải danh sách bạn bè
async function loadFriends() {
    if (!userInfo.value) return;
    try {
        const token = localStorage.getItem("token");
        const res = await axios.get(`${USER_SERVICE_URL}friends/${userInfo.value.user_id}/accepted`, {
            headers: { Authorization: `Bearer ${token}` }
        });
        
        // Lấy profile chi tiết cho từng bạn
        friends.value = await Promise.all(res.data.map(async (f: any) => {
            const friendId = f.user_id === userInfo.value.user_id ? f.friend_id : f.user_id;
            const profile = await getProfile(friendId);
            return {
                id: friendId,
                username: profile?.username || 'Bạn bè',
                avatar: profile?.avatar_url
            };
        }));
    } catch (e) {
        console.error("Lỗi tải bạn bè:", e);
    } finally {
        loading.value = false;
    }
}

// 2. Gửi lời giới thiệu (Tạo Notification)
async function sendRecommendation() {
    if (selectedFriends.value.length === 0) return alert("Chọn ít nhất 1 người bạn!");
    
    sending.value = true;
    try {
        const payload = {
            bookId: props.bookId,
            bookTitle: props.bookTitle,
            note: message.value // Lời nhắn kèm theo
        };

        // Gửi song song cho từng người
        await Promise.all(selectedFriends.value.map(friendId => 
            axios.post(`${USER_SERVICE_URL}notifications/add`, {
                receiver_id: friendId,
                sender_id: userInfo.value.user_id,
                type: 'book_recommendation', // Loại thông báo mới
                message: JSON.stringify(payload),
                status: 'unread'
            })
        ));

        alert("Đã gửi giới thiệu thành công!");
        emit('close');
    } catch (e) {
        alert("Lỗi khi gửi giới thiệu.");
    } finally {
        sending.value = false;
    }
}

onMounted(loadFriends);
</script>

<template>
    <div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4 backdrop-blur-sm" @click.self="$emit('close')">
        <div class="bg-white rounded-xl shadow-2xl w-full max-w-md overflow-hidden flex flex-col max-h-[80vh]">
            <div class="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
                <h3 class="font-bold text-gray-800">Gửi tặng sách này 🎁</h3>
                <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">✕</button>
            </div>

            <div class="p-4 flex-1 overflow-y-auto custom-scrollbar">
                <p class="text-sm text-gray-600 mb-4">
                    Giới thiệu cuốn <span class="font-bold text-indigo-600">"{{ bookTitle }}"</span> cho bạn bè:
                </p>

                <div v-if="loading" class="text-center py-4 text-gray-500">Đang tải danh sách bạn...</div>
                
                <div v-else-if="friends.length === 0" class="text-center py-4 text-gray-500 italic">
                    Bạn chưa có bạn bè nào để gửi.
                </div>

                <div v-else class="space-y-2">
                    <label v-for="friend in friends" :key="friend.id" 
                           class="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-pointer border border-transparent hover:border-gray-200 transition">
                        <input type="checkbox" :value="friend.id" v-model="selectedFriends" class="w-4 h-4 text-indigo-600 rounded focus:ring-indigo-500">
                        
                        <img v-if="friend.avatar" :src="`${AVATAR_SERVER_URL}/${friend.avatar}`" class="w-8 h-8 rounded-full object-cover">
                        <div v-else class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold text-xs">
                            {{ friend.username.charAt(0).toUpperCase() }}
                        </div>
                        
                        <span class="text-sm font-medium text-gray-700">{{ friend.username }}</span>
                    </label>
                </div>
            </div>

            <div class="p-4 border-t border-gray-100 bg-gray-50">
                <textarea v-model="message" rows="2" class="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-indigo-500 outline-none mb-3" placeholder="Viết lời nhắn (Ví dụ: Cuốn này hợp với cậu lắm)..."></textarea>
                
                <button @click="sendRecommendation" :disabled="sending || selectedFriends.length === 0" 
                        class="w-full py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed">
                    {{ sending ? 'Đang gửi...' : 'Gửi ngay' }}
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 4px; }
</style>