<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import Navbar from '../components/layout/Navbar.vue';
import { USER_SERVICE_URL, AVATAR_SERVER_URL } from '../config';
import { useAuth } from '../composables/useAuth'; 
import { getProfile } from '../composables/useProfile'; 

// --- Types ---
interface FriendRelationship {
    id: number;           
    user_id: number;      
    friend_id: number;    
    status: string;
    created_at: string;
}

interface FriendDisplay extends FriendRelationship {
    partnerInfo: {
        id: number;
        username: string;
        avatar_url: string | null;
        full_name: string | null;
    } | null;
}

// --- State ---
const { userInfo } = useAuth();
const activeTab = ref<'friends' | 'incoming' | 'outgoing'>('friends');
const loading = ref(false);

const friendsList = ref<FriendDisplay[]>([]);
const incomingRequests = ref<FriendDisplay[]>([]);
const outgoingRequests = ref<FriendDisplay[]>([]);

// --- Helper Functions ---

async function enrichFriendData(relationships: FriendRelationship[]) {
    if (!userInfo.value) return [];

    const promises = relationships.map(async (rel) => {
        const isMeSender = rel.user_id === userInfo.value.user_id;
        const partnerId = isMeSender ? rel.friend_id : rel.user_id;

        const profileData = await getProfile(partnerId);
        
        const finalProfile = profileData || {
            id: partnerId,
            username: `User ${partnerId}`,
            avatar_url: null,
            full_name: null
        };

        return {
            ...rel,
            partnerInfo: finalProfile
        } as FriendDisplay;
    });

    return await Promise.all(promises);
}

// --- Main Data Fetching ---

async function fetchFriendsData() {
    if (!userInfo.value) return;
    loading.value = true;
    const token = localStorage.getItem('token');
    const headers = { Authorization: `Bearer ${token}` };
    const myId = userInfo.value.user_id;

    try {
        // 1. Friends
        try {
            const resAccepted = await axios.get(`${USER_SERVICE_URL}friends/${myId}/accepted`, { headers });
            friendsList.value = await enrichFriendData(resAccepted.data);
        } catch (e) { friendsList.value = []; }

        // 2. Pending
        try {
            const resPending = await axios.get(`${USER_SERVICE_URL}friends/${myId}/pending`, { headers });
            const allPending = await enrichFriendData(resPending.data);

            incomingRequests.value = allPending.filter(f => f.user_id !== myId);
            outgoingRequests.value = allPending.filter(f => f.user_id === myId);
        } catch (e) {
            incomingRequests.value = [];
            outgoingRequests.value = [];
        }
    } catch (error) { console.error(error); } finally { loading.value = false; }
}

// --- Actions ---

async function acceptRequest(relationshipId: number) {
    try {
        const token = localStorage.getItem('token');
        await axios.put(`${USER_SERVICE_URL}friends/update/${relationshipId}?status=accepted`, {}, { headers: { Authorization: `Bearer ${token}` } });
        await fetchFriendsData();
    } catch (error) { alert("Có lỗi khi chấp nhận kết bạn"); }
}

async function deleteRelationship(relationshipId: number) {
    if (!confirm("Bạn có chắc chắn muốn thực hiện thao tác này?")) return;
    try {
        const token = localStorage.getItem('token');
        await axios.delete(`${USER_SERVICE_URL}friends/delete/${relationshipId}`, { headers: { Authorization: `Bearer ${token}` } });
        await fetchFriendsData();
    } catch (error) { alert("Có lỗi khi xóa bạn bè"); }
}

onMounted(() => { fetchFriendsData(); });
</script>

<template>
    <Navbar />
    
    <div class="min-h-screen bg-gray-50 py-8">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 class="text-3xl font-bold text-gray-800 mb-6">Bạn bè</h1>

            <div class="flex border-b border-gray-200 mb-6">
                <button @click="activeTab = 'friends'" :class="['px-6 py-3 font-medium text-sm transition-colors', activeTab === 'friends' ? 'border-b-2 border-yellow-500 text-yellow-600' : 'text-gray-500 hover:text-gray-700']">
                    Bạn bè ({{ friendsList.length }})
                </button>
                <button @click="activeTab = 'incoming'" :class="['px-6 py-3 font-medium text-sm transition-colors', activeTab === 'incoming' ? 'border-b-2 border-yellow-500 text-yellow-600' : 'text-gray-500 hover:text-gray-700']">
                    Lời mời kết bạn <span v-if="incomingRequests.length" class="ml-1 bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">{{ incomingRequests.length }}</span>
                </button>
                <button @click="activeTab = 'outgoing'" :class="['px-6 py-3 font-medium text-sm transition-colors', activeTab === 'outgoing' ? 'border-b-2 border-yellow-500 text-yellow-600' : 'text-gray-500 hover:text-gray-700']">
                    Đã gửi ({{ outgoingRequests.length }})
                </button>
            </div>

            <div v-if="loading" class="text-center py-10 text-gray-500">Đang tải dữ liệu...</div>

            <div v-else>
                <div v-if="activeTab === 'friends'">
                    <div v-if="friendsList.length === 0" class="text-center py-10 bg-white rounded-lg shadow-sm text-gray-500">Bạn chưa có người bạn nào.</div>
                    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div v-for="friend in friendsList" :key="friend.id" class="bg-white p-4 rounded-lg shadow-sm flex items-center justify-between">
                            <div class="flex items-center space-x-3 cursor-pointer" @click="$router.push(`/profile/${friend.partnerInfo?.id}`)">
                                
                                <img v-if="friend.partnerInfo?.avatar_url" 
                                    :src="`${AVATAR_SERVER_URL}/${friend.partnerInfo.avatar_url}`" 
                                    class="w-12 h-12 rounded-full object-cover border border-gray-200">
                                
                                <div v-else 
                                    class="w-12 h-12 rounded-full border border-gray-300 bg-yellow-400 flex items-center justify-center shrink-0">
                                    <span class="text-xl font-semibold text-white">
                                        {{ friend.partnerInfo?.username?.charAt(0).toUpperCase() }}
                                    </span>
                                </div>
                                <div>
                                    <h3 class="font-semibold text-gray-800">{{ friend.partnerInfo?.full_name || friend.partnerInfo?.username }}</h3>
                                    <p class="text-xs text-gray-500">@{{ friend.partnerInfo?.username }}</p>
                                </div>
                            </div>
                            <button @click="deleteRelationship(friend.id)" class="text-sm text-red-500 hover:bg-red-50 px-3 py-1.5 rounded border border-red-200">Hủy</button>
                        </div>
                    </div>
                </div>

                <div v-if="activeTab === 'incoming'">
                    <div v-if="incomingRequests.length === 0" class="text-center py-10 bg-white rounded-lg shadow-sm text-gray-500">Không có lời mời nào.</div>
                    <div v-else class="space-y-3">
                        <div v-for="req in incomingRequests" :key="req.id" class="bg-white p-4 rounded-lg shadow-sm flex items-center justify-between">
                            <div class="flex items-center space-x-3 cursor-pointer" @click="$router.push(`/profile/${req.partnerInfo?.id}`)">
                                
                                <img v-if="req.partnerInfo?.avatar_url" 
                                    :src="`${AVATAR_SERVER_URL}/${req.partnerInfo.avatar_url}`" 
                                    class="w-12 h-12 rounded-full object-cover border border-gray-200">
                                
                                <div v-else 
                                    class="w-12 h-12 rounded-full border border-gray-300 bg-yellow-400 flex items-center justify-center shrink-0">
                                    <span class="text-xl font-semibold text-white">
                                        {{ req.partnerInfo?.username?.charAt(0).toUpperCase() }}
                                    </span>
                                </div>
                                <div>
                                    <h3 class="font-semibold text-gray-800"><span class="font-bold">{{ req.partnerInfo?.full_name || req.partnerInfo?.username }}</span> muốn kết bạn</h3>
                                    <p class="text-xs text-gray-400">{{ new Date(req.created_at).toLocaleDateString() }}</p>
                                </div>
                            </div>
                            <div class="flex gap-2">
                                <button @click="acceptRequest(req.id)" class="bg-yellow-500 text-white px-4 py-1.5 rounded text-sm hover:bg-yellow-600 font-medium">Chấp nhận</button>
                                <button @click="deleteRelationship(req.id)" class="bg-gray-200 text-gray-700 px-4 py-1.5 rounded text-sm hover:bg-gray-300 font-medium">Từ chối</button>
                            </div>
                        </div>
                    </div>
                </div>

                <div v-if="activeTab === 'outgoing'">
                    <div v-if="outgoingRequests.length === 0" class="text-center py-10 bg-white rounded-lg shadow-sm text-gray-500">Chưa gửi lời mời nào.</div>
                    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div v-for="req in outgoingRequests" :key="req.id" class="bg-white p-4 rounded-lg shadow-sm flex items-center justify-between opacity-90">
                            <div class="flex items-center space-x-3 cursor-pointer" @click="$router.push(`/profile/${req.partnerInfo?.id}`)">
                                
                                <img v-if="req.partnerInfo?.avatar_url" 
                                    :src="`${AVATAR_SERVER_URL}/${req.partnerInfo.avatar_url}`" 
                                    class="w-10 h-10 rounded-full object-cover border border-gray-200 grayscale">
                                
                                <div v-else 
                                    class="w-10 h-10 rounded-full border border-gray-300 bg-yellow-400 flex items-center justify-center shrink-0 grayscale">
                                    <span class="text-lg font-semibold text-white">
                                        {{ req.partnerInfo?.username?.charAt(0).toUpperCase() }}
                                    </span>
                                </div>
                                <div>
                                    <h3 class="font-medium text-gray-700">{{ req.partnerInfo?.full_name || req.partnerInfo?.username }}</h3>
                                    <p class="text-xs text-gray-500">Đã gửi yêu cầu</p>
                                </div>
                            </div>
                            <button @click="deleteRelationship(req.id)" class="text-xs text-gray-500 hover:text-red-500 border border-gray-300 hover:border-red-400 px-3 py-1 rounded">Hủy</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>