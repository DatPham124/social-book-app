<script setup lang="ts">
import { ref, onMounted, Ref, computed } from "vue";
import axios from "axios";
import { BOOK_SERVICE_URL, AVATAR_SERVER_URL, COVER_IMAGE_SERVER_URL, USER_SERVICE_URL } from "../../../config";
import { useAuth } from "../../../composables/useAuth";
import { getProfile } from "../../../composables/useProfile";
import { useBooks } from "../../../composables/useBook";
import { useRoute, useRouter } from "vue-router";
import Navbar from "../../layout/Navbar.vue";

const route = useRoute();
const router = useRouter();
const buddyReadId = Number(route.params.id);

const { userInfo } = useAuth();
const { getBookById } = useBooks();

// ... Interface giữ nguyên ...
interface Profile { user_id: number; username: string; avatar_url?: string; }
interface Book { id: number; title: string; cover_url?: string; author?: string; }
interface BuddyRead { id: number; book_id: number; created_by_user_id: number; book?: Book; }
interface Comment { id: number; content: string; created_at: string; user_id: number; user?: Profile; }
interface SearchUser { id: number; username: string; }

const buddyRead = ref<BuddyRead | null>(null);
const comments = ref<Comment[]>([]);
const members = ref<Profile[]>([]);
const newComment = ref("");
const loading = ref(true);
const isPostingComment = ref(false);

const showMenu = ref(false);
const isDeleting = ref(false);
const showInviteModal = ref(false);
const searchQuery = ref("");
const searchResults = ref<SearchUser[]>([]);
const isSearching = ref(false);
const inviteMessage = ref("");

const lastCommentNotifTime = ref(0);
const COMMENT_NOTIF_COOLDOWN = 5 * 60 * 1000; 

const isCreatorOfBuddyRead = computed(() => {
  if (!userInfo.value || !buddyRead.value) return false;
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  return userId === buddyRead.value.created_by_user_id;
});

const memberNames = computed(() => {
  if (members.value.length === 0) return "bạn bè";
  const currentUserId = userInfo.value?.id || userInfo.value?.user_id;
  const otherMembers = members.value.filter(m => m.user_id !== currentUserId);
  if (otherMembers.length === 0) return "chính bạn";
  return otherMembers.map(m => m.username).join(', ');
});

// --- HÀM FORMAT NGÀY GIỜ CHUẨN ---
function formatCommentTime(dateStr: string) {
    if (!dateStr) return '';
    // Thêm 'Z' nếu chưa có để trình duyệt hiểu là UTC
    const date = !dateStr.endsWith('Z') ? new Date(dateStr + 'Z') : new Date(dateStr);
    return date.toLocaleString('vi-VN', {
        hour: '2-digit', minute: '2-digit',
        day: '2-digit', month: '2-digit', year: 'numeric'
    });
}

async function loadBuddyRead() {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}buddyreads/${buddyReadId}`);
    const readData = res.data;
    const bookData = await getBookById(readData.book_id);
    buddyRead.value = { ...readData, book: bookData };
  } catch (error) { console.error(error); }
}

async function loadComments() {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}buddyreads/${buddyReadId}/comments`);
    const commentsWithProfile = await Promise.all(
      res.data.map(async (comment: Comment) => {
        const profile = await getProfile(comment.user_id);
        return { ...comment, user: profile };
      })
    );
    comments.value = commentsWithProfile;
  } catch (error) { console.error(error); }
}

async function loadMembers() {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}buddyreads/${buddyReadId}/members`);
    const membersWithProfile = await Promise.all(
      res.data.map(async (member: { user_id: number }) => {
        return await getProfile(member.user_id);
      })
    );
    members.value = membersWithProfile.filter(p => p != null); 
  } catch (error) { console.error(error); }
}

// ... Giữ nguyên các hàm sendCommentNotification, postComment, deleteBuddyRead, leaveBuddyRead, openInviteModal, searchUsers, sendInvite ...
// (Đã có sẵn trong file cũ của bạn, không cần thay đổi logic)

async function sendCommentNotification() {
  const now = Date.now();
  if (now - lastCommentNotifTime.value < COMMENT_NOTIF_COOLDOWN) return;
  lastCommentNotifTime.value = now;
  
  const currentUserId = userInfo.value?.id || userInfo.value?.user_id;
  const bookTitle = buddyRead.value?.book?.title || "một cuốn sách";
  const receivers = members.value.filter(m => m.user_id !== currentUserId);

  for (const member of receivers) {
    try {
      await axios.post(`${USER_SERVICE_URL}notifications/add`, {
        receiver_id: member.user_id,
        sender_id: currentUserId,
        type: 'buddy_comment', 
        message: `đã bình luận trong nhóm đọc "${bookTitle}"`, // Nội dung rút gọn
        status: 'unread'
      });
    } catch (e) { console.error(e); }
  }
}

async function postComment() {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!newComment.value.trim() || !userId) return;
  
  isPostingComment.value = true;
  try {
    const formData = new FormData();
    formData.append("content", newComment.value);
    formData.append("user_id", String(userId));
    await axios.post(`${BOOK_SERVICE_URL}buddyreads/${buddyReadId}/comments`, formData);
    newComment.value = "";
    await loadComments(); 
    sendCommentNotification();
  } catch (err: any) { alert(err.response?.data?.detail || "Lỗi"); } 
  finally { isPostingComment.value = false; }
}

async function deleteBuddyRead() {
  if (!confirm("Xóa phòng đọc?")) return;
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId) return;
  isDeleting.value = true;
  try {
    const formData = new FormData();
    formData.append("user_id", String(userId));
    await axios.delete(`${BOOK_SERVICE_URL}buddyreads/${buddyReadId}`, { data: formData });
    router.push('/community'); 
  } catch (err: any) { alert("Lỗi khi xóa"); } finally { isDeleting.value = false; }
}

async function leaveBuddyRead() {
  if (!confirm("Rời phòng đọc?")) return;
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!userId) return;
  isDeleting.value = true;
  try {
    const formData = new FormData();
    formData.append("user_id", String(userId));
    await axios.delete(`${BOOK_SERVICE_URL}buddyreads/${buddyReadId}/leave`, { data: formData });
    router.push('/community'); 
  } catch (err: any) { alert("Lỗi khi rời"); } finally { isDeleting.value = false; }
}

function openInviteModal() {
  showInviteModal.value = true; showMenu.value = false; searchQuery.value = ""; searchResults.value = []; inviteMessage.value = "";
}

async function searchUsers() {
  if (searchQuery.value.length < 2) { searchResults.value = []; return; }
  isSearching.value = true; inviteMessage.value = "";
  try {
    const res = await axios.get(`${USER_SERVICE_URL}users/search`, { params: { query: searchQuery.value } });
    const currentUserId = userInfo.value?.id || userInfo.value?.user_id;
    const memberIds = members.value.map(m => m.user_id);
    searchResults.value = res.data.filter((user: SearchUser) => user.id !== currentUserId && !memberIds.includes(user.id));
  } catch (err) { console.error(err); } finally { isSearching.value = false; }
}

async function sendInvite(inviteeId: number) {
  inviteMessage.value = "Đang gửi...";
  const senderId = userInfo.value?.id || userInfo.value?.user_id;
  try {
    const formData = new FormData();
    formData.append("invitee_id", String(inviteeId));
    formData.append("sender_id", String(senderId)); 
    await axios.post(`${BOOK_SERVICE_URL}buddyreads/${buddyReadId}/invite`, formData);
    inviteMessage.value = "Đã gửi lời mời!";
    searchResults.value = searchResults.value.filter(user => user.id !== inviteeId);
  } catch (err: any) { inviteMessage.value = "Lỗi gửi lời mời"; }
}

onMounted(async () => {
  loading.value = true;
  await Promise.all([loadBuddyRead(), loadComments(), loadMembers()]);
  loading.value = false;
});
</script>

<template>
  <Navbar />
  <div class="max-w-3xl mx-auto p-4 sm:p-6 mt-8">
    <!-- ... Phần Header giữ nguyên ... -->
    <div v-if="loading" class="text-center text-gray-500 py-10">Đang tải...</div>
    <div v-else-if="!buddyRead" class="text-center text-red-500 py-10">Không tìm thấy phòng đọc.</div>

    <div v-else>
      <button @click="router.push('/community')" class="text-sm font-medium text-yellow-600 hover:text-yellow-800 mb-4">&larr; Quay lại Cộng đồng</button>

      <div class="bg-white p-5 border rounded-lg shadow-sm">
        <div class="flex justify-between items-start">
          <p class="text-sm font-semibold text-yellow-600">ĐỌC CÙNG BẠN</p>
          <div class="relative">
            <button @click="showMenu = !showMenu" class="text-gray-500 hover:text-gray-700 text-2xl font-bold px-2 -mt-2">⋮</button>
            <div v-if="showMenu" class="absolute right-0 mt-2 w-48 bg-white border rounded-md shadow-lg z-10">
              <button v-if="isCreatorOfBuddyRead" @click="openInviteModal" class="block w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-yellow-50 rounded-t-md">Mời thành viên</button>
              <button v-if="isCreatorOfBuddyRead" @click="deleteBuddyRead" :disabled="isDeleting" class="block w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-b-md disabled:opacity-50">{{ isDeleting ? 'Đang xóa...' : 'Xóa phòng đọc' }}</button>
              <button v-else @click="leaveBuddyRead" :disabled="isDeleting" class="block w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-md disabled:opacity-50">{{ isDeleting ? 'Đang rời...' : 'Rời khỏi phòng đọc' }}</button>
            </div>
          </div>
        </div>
        
        <div class="flex items-center gap-4 mt-1">
          <img v-if="buddyRead.book?.cover_url" :src="`${COVER_IMAGE_SERVER_URL}/${buddyRead.book.cover_url}`" class="w-16 h-24 object-cover rounded shadow-sm"/>
          <div v-else class="w-16 h-24 bg-gray-200 rounded flex items-center justify-center text-3xl text-gray-400">📚</div>
          <div>
            <h2 class="text-2xl font-bold text-gray-900">{{ buddyRead.book?.title }}</h2>
            <p class="text-gray-600 mt-1">Đọc cùng <span class="font-medium">{{ memberNames }}</span></p>
            <router-link :to="`/buddy-read/${buddyReadId}/room`" class="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-full shadow-md transition-transform transform hover:scale-105">
              <span>🎧</span> Vào Phòng Đọc Chung (Live)
            </router-link>
          </div>
        </div>
      </div>

      <div class="mt-8">
        <h3 class="text-lg font-semibold text-gray-700 mb-4">Thảo luận ({{ comments.length }})</h3>
        
        <div v-if="comments.length === 0" class="text-center text-gray-500 py-10 italic">Chưa có bình luận nào.</div>

        <div v-else class="space-y-4">
          <div v-for="comment in comments" :key="comment.id" class="flex gap-3">
            <div class="w-9 h-9 rounded-full bg-gray-200 flex items-center justify-center font-semibold text-yellow-600 overflow-hidden flex-shrink-0">
              <img v-if="comment.user?.avatar_url" :src="`${AVATAR_SERVER_URL}/${comment.user.avatar_url}`" class="w-full h-full object-cover" />
              <span v-else class="text-sm">{{ comment.user?.username.charAt(0).toUpperCase() || 'A' }}</span>
            </div>
            <div class="flex-1 bg-gray-50 rounded-lg p-3 border">
              <p class="text-sm">
                <span class="font-semibold text-gray-800">{{ comment.user?.username }}</span>
                <!-- SỬA Ở ĐÂY: Dùng hàm formatCommentTime -->
                <span class="text-gray-400 ml-2 text-xs">{{ formatCommentTime(comment.created_at) }}</span>
              </p>
              <p class="text-gray-700 whitespace-pre-line mt-1">{{ comment.content }}</p>
            </div>
          </div>
        </div>

        <div class="mt-6 border-t pt-6">
          <h4 class="font-semibold text-gray-700 mb-2">Thêm bình luận</h4>
          <textarea v-model="newComment" rows="3" class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none" placeholder="Viết bình luận của bạn..."></textarea>
          <button @click="postComment" :disabled="isPostingComment" class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md mt-3 disabled:opacity-50 disabled:cursor-not-allowed">
            {{ isPostingComment ? 'Đang gửi...' : 'Gửi bình luận' }}
          </button>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Modal Mời bạn bè (Giữ nguyên) -->
  <div v-if="showInviteModal" @click.self="showInviteModal = false" class="fixed inset-0 bg-opacity-30 backdrop-blur-sm flex justify-center items-center z-50 p-4">
    <div class="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
      <h3 class="text-lg font-semibold text-gray-800 mb-4">Mời bạn bè vào phòng đọc</h3>
      <input v-model="searchQuery" @input="searchUsers" type="text" class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none" placeholder="Tìm bạn bè theo username..." />
      <div v-if="isSearching" class="text-gray-500 text-center py-3">Đang tìm...</div>
      <ul v-if="searchResults.length > 0" class="mt-4 max-h-60 overflow-y-auto space-y-2">
        <li v-for="user in searchResults" :key="user.id" class="flex justify-between items-center p-2 border rounded-md hover:bg-gray-50">
          <span class="font-medium text-gray-700">{{ user.username }}</span>
          <button @click="sendInvite(user.id)" class="px-3 py-1 bg-yellow-400 hover:bg-yellow-500 text-black text-sm font-semibold rounded-md">Mời</button>
        </li>
      </ul>
      <p v-if="inviteMessage" class="text-sm text-green-600 mt-3">{{ inviteMessage }}</p>
      <div class="flex justify-end mt-5">
        <button @click="showInviteModal = false" class="px-4 py-2 border border-gray-400 rounded-md text-gray-600 hover:bg-gray-100">Đóng</button>
      </div>
    </div>
  </div>
</template>