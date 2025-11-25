<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { AVATAR_SERVER_URL } from '../../../config';
import { 
    collection, addDoc, query, orderBy, limit, 
    onSnapshot, serverTimestamp, doc, setDoc, 
    deleteDoc, getDocs, writeBatch 
} from "firebase/firestore";

import { db } from '../../../firebase'; 

const props = defineProps<{
    roomId: string;
    userInfo: any;
}>();


const messages = ref<any[]>([]);
const onlineUsers = ref<any[]>([]);
const newMessage = ref("");
const chatContainer = ref<HTMLElement | null>(null);
let unsubscribeMessages: any = null;
let unsubscribeUsers: any = null;

async function updateUserStatus(status: string) {
    if (!props.userInfo) return;
    const userRef = doc(db, "rooms", props.roomId, "users", String(props.userInfo.user_id));
    try {
        await setDoc(userRef, {
            id: props.userInfo.user_id, 
            username: props.userInfo.username, 
            avatar: props.userInfo.avatar_url || null,
            status: status, 
            last_active: serverTimestamp()
        }, { merge: true });
    } catch (e) { console.error("Lỗi update status:", e); }
}

defineExpose({ updateUserStatus });

async function sendMessage() {
    if (!newMessage.value.trim() || !props.userInfo) return;
    try {
        await addDoc(collection(db, "rooms", props.roomId, "messages"), {
            text: newMessage.value, 
            user_id: props.userInfo.user_id, 
            username: props.userInfo.username,
            avatar: props.userInfo.avatar_url || null, 
            created_at: serverTimestamp()
        });
        newMessage.value = "";
    } catch (e) { console.error("Lỗi gửi tin nhắn:", e); }
}

async function leaveRoom() {
    if (props.userInfo) {
        const userRef = doc(db, "rooms", props.roomId, "users", String(props.userInfo.user_id));
        await deleteDoc(userRef);

        // Logic xóa phòng nếu rỗng (giữ nguyên)
        const usersSnap = await getDocs(collection(db, "rooms", props.roomId, "users"));
        if (usersSnap.empty) {
            const messagesRef = collection(db, "rooms", props.roomId, "messages");
            const msgSnap = await getDocs(messagesRef);
            const batch = writeBatch(db);
            msgSnap.docs.forEach((doc) => batch.delete(doc.ref));
            await batch.commit();
        }
    }
}

onMounted(() => {
    updateUserStatus("idle");

    const usersQ = query(collection(db, "rooms", props.roomId, "users"));
    unsubscribeUsers = onSnapshot(usersQ, (snap) => onlineUsers.value = snap.docs.map(d => d.data()));

    const msgQ = query(collection(db, "rooms", props.roomId, "messages"), orderBy("created_at", "asc"), limit(100));
    unsubscribeMessages = onSnapshot(msgQ, (snap) => {
        messages.value = snap.docs.map(d => ({ id: d.id, ...d.data() }));
        nextTick(() => chatContainer.value && (chatContainer.value.scrollTop = chatContainer.value.scrollHeight));
    });

    window.addEventListener('beforeunload', leaveRoom);
});

onUnmounted(() => {
    if (unsubscribeMessages) unsubscribeMessages();
    if (unsubscribeUsers) unsubscribeUsers();
    window.removeEventListener('beforeunload', leaveRoom);
    leaveRoom();
});
</script>

<template>
  <!-- Template giữ nguyên 100% -->
  <div class="flex flex-col gap-6 h-full">
        <!-- Online Users -->
        <div class="bg-gray-50 rounded-xl border p-4 h-40 overflow-y-auto">
            <h3 class="text-sm font-bold text-gray-500 mb-3 flex items-center gap-2">👥 Thành viên ({{ onlineUsers.length }})</h3>
            <div class="grid grid-cols-2 gap-3">
                <div v-for="user in onlineUsers" :key="user.id" class="flex items-center gap-2 p-2 bg-white rounded shadow-sm border">
                    <div class="relative">
                        <img v-if="user.avatar" :src="`${AVATAR_SERVER_URL}/${user.avatar}`" class="w-8 h-8 rounded-full object-cover" />
                        <div v-else class="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-xs font-bold text-indigo-600">
                            {{ user.username?.charAt(0).toUpperCase() }}
                        </div>
                        
                        <span class="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-white"
                            :class="{ 'bg-green-500': user.status === 'focus', 'bg-blue-400': user.status === 'break', 'bg-gray-400': user.status === 'idle' || user.status === 'paused' }">
                        </span>
                    </div>
                    <div class="truncate text-xs font-medium">{{ user.username }}</div>
                </div>
            </div>
        </div>

        <!-- Chat -->
        <div class="flex flex-col bg-white rounded-2xl shadow-lg border overflow-hidden flex-1">
            <div class="p-4 border-b font-bold text-gray-700 text-sm">💬 Chat Nhóm</div>
            <div ref="chatContainer" class="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
                <div v-for="msg in messages" :key="msg.id" class="flex gap-2"
                    :class="{ 'flex-row-reverse': msg.user_id === props.userInfo.user_id }">
                    <div class="flex-shrink-0 mt-1">
                        <!-- Logic hiển thị Avatar trong Chat -->
                        <img v-if="msg.avatar" :src="`${AVATAR_SERVER_URL}/${msg.avatar}`" class="w-6 h-6 rounded-full object-cover" />
                        <div v-else class="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-[10px] font-bold text-gray-600">
                            {{ msg.username?.charAt(0).toUpperCase() }}
                        </div>
                    </div>
                    <div class="max-w-[85%] px-3 py-2 rounded-xl text-sm"
                        :class="msg.user_id === props.userInfo.user_id ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-gray-100 text-gray-800 rounded-tl-none'">
                        {{ msg.text }}
                    </div>
                </div>
            </div>
            <div class="p-3 border-t bg-gray-50">
                <form @submit.prevent="sendMessage" class="flex gap-2">
                    <input v-model="newMessage" class="flex-1 border rounded-full px-3 py-2 text-sm" placeholder="Chat..." />
                    <button type="submit" class="text-indigo-600 hover:text-indigo-800 font-bold px-2">Gửi</button>
                </form>
            </div>
        </div>
    </div>
</template>