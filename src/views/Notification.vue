<script setup lang="ts">
import { ref, onMounted } from "vue";
import Navbar from "../components/layout/Navbar.vue";
import { AVATAR_SERVER_URL, USER_SERVICE_URL, BOOK_SERVICE_URL } from "../config";
import { getProfile } from "../composables/useProfile";
import { useAuth } from "../composables/useAuth";
import { useBooks } from "../composables/useBook"; 
import axios from "axios";

const { userInfo } = useAuth();
const { getBookById } = useBooks();

const notifyList = ref<any[]>([]);
const dangTai = ref(true);
const loi = ref<string | null>(null);

function dinhDangThoiGian(thoiGianStr: string) {
  // Fix lỗi hiển thị thời gian nếu backend trả về UTC không có Z
  const dateStr = !thoiGianStr.endsWith('Z') ? thoiGianStr + 'Z' : thoiGianStr;
  const diffMs = Date.now() - new Date(dateStr).getTime(); 
  const phut = Math.floor(diffMs / 60000);
  if (phut < 1) return "vừa xong";
  if (phut < 60) return `${phut} phút trước`;
  const gio = Math.floor(phut / 60);
  if (gio < 24) return `${gio} giờ trước`;
  const ngay = Math.floor(gio / 24);
  return `${ngay} ngày trước`;
}

const token = localStorage.getItem("token");

// --- CÁC HÀM XỬ LÝ API ---

async function rejectFriendRequest(tb: any) {
  try {
    await axios.delete(`${USER_SERVICE_URL}friends/delete/${tb.message}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    await deleteNotification(tb.id);
  } catch (err: any) {
    console.error("Lỗi:", err);
  }
}
async function acceptFriendRequest(friendId: number) {
  try {
    await axios.put(
      `${USER_SERVICE_URL}friends/update/${friendId}?status=accepted`,
      {},
      { headers: { Authorization: `Bearer ${token}` } }
    );
    const index = notifyList.value.findIndex(
      (tb) => tb.message == String(friendId) && tb.type === 'friend_request'
    );
    if (index !== -1) {
      notifyList.value[index].status = 'accepted';
    }
  } catch (err: any) {
    console.error("Lỗi:", err);
  }
}
async function checkFriendStatus(friendId?: number) {
  if (!token || !userInfo || !friendId) return null;
  try {
    const response = await axios.get(`${USER_SERVICE_URL}friends/${friendId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) { return null; }
}

async function getClub(clubId: number) {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${clubId}`);
    return res.data;
  } catch (error) { return null; }
}
async function acceptBookClubInvite(invitationId: number) {
  try {
    await axios.post(`${BOOK_SERVICE_URL}bookclubs/invitations/${invitationId}/accept`);
    notifyList.value = notifyList.value.filter(n => n.id !== invitationId || n.type !== 'bookclub_invite');
  } catch (err: any) { loi.value = "Lỗi khi tham gia club"; }
}
async function rejectBookClubInvite(invitationId: number) {
  try {
    await axios.delete(`${BOOK_SERVICE_URL}bookclubs/invitations/${invitationId}/decline`);
    notifyList.value = notifyList.value.filter(n => n.id !== invitationId || n.type !== 'bookclub_invite');
  } catch (err) { console.error("Lỗi:", err); }
}

async function acceptBuddyReadInvite(invitationId: number) {
  try {
    await axios.post(`${BOOK_SERVICE_URL}buddyreads/invitations/${invitationId}/accept`);
    notifyList.value = notifyList.value.filter(n => n.id !== invitationId || n.type !== 'buddy_read_invite');
  } catch (err: any) { loi.value = "Lỗi khi chấp nhận"; }
}
async function rejectBuddyReadInvite(invitationId: number) {
  try {
    await axios.delete(`${BOOK_SERVICE_URL}buddyreads/invitations/${invitationId}/decline`);
    notifyList.value = notifyList.value.filter(n => n.id !== invitationId || n.type !== 'buddy_read_invite');
  } catch (err) { console.error("Lỗi:", err); }
}

async function deleteNotification(notificationId: number) {
  try {
    await axios.delete(`${USER_SERVICE_URL}notifications/${notificationId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    notifyList.value = notifyList.value.filter(n => n.id !== notificationId);
  } catch (err) { console.error("Lỗi:", err); }
}

// --- HÀM LOAD DỮ LIỆU ---

async function loadNotify(userId: number) {
  try {
    const [friendNotifyRes, clubInviteRes, buddyReadInviteRes] = await Promise.all([
      axios.get(`${USER_SERVICE_URL}notifications/user/${userId}`),
      axios.get(`${BOOK_SERVICE_URL}bookclubs/invitations/${userId}`),
      axios.get(`${BOOK_SERVICE_URL}buddyreads/invitations/${userId}`)
    ]);

    // 1. Xử lý Thông báo User (Gồm cả Chat, Comment, CLB, Like Quote...)
    const processedUserNotifs = await Promise.all(
      friendNotifyRes.data.map(async (item: any) => {
        const senderProfile = await getProfile(item.sender_id);
        let friend_record = null;
        let displayContent = item.message; 
        let relatedBookId = null; // Biến để lưu ID sách nếu có

        // A. Xử lý Friend Request
        if (item.type === 'friend_request') {
          const fid = Number(item.message);
          friend_record = await checkFriendStatus(fid);
        }
        
        // B. Xử lý các thông báo dạng JSON (Chat, CLB, Buddy Comment...)
        else if (item.message && item.message.startsWith('{')) {
            try {
                const parsed = JSON.parse(item.message);
                
                if (item.type === 'buddy_chat') {
                    displayContent = parsed.text;
                }
                // --- CÁC LOẠI THÔNG BÁO CLB ---
                else if (item.type === 'club_meeting') {
                    displayContent = `đã tạo cuộc họp "${parsed.title}" trong CLB ${parsed.clubName}`;
                }
                else if (item.type === 'club_discussion') {
                    displayContent = `đã tạo thảo luận "${parsed.title}" trong CLB ${parsed.clubName}`;
                }
                else if (item.type === 'club_comment') {
                    displayContent = `đã bình luận trong bài "${parsed.discussionTitle}": "${parsed.content}"`;
                }
                else if (item.type === 'club_join_request') {
                    displayContent = `muốn tham gia câu lạc bộ "${parsed.clubName}"`;
                }
                else if (item.type === 'club_join_accepted') {
                    displayContent = `đã duyệt yêu cầu tham gia CLB "${parsed.clubName}"`;
                }
                else if (item.type === 'quote_like') {
                    displayContent = `đã thích trích dẫn của bạn trong sách "${parsed.bookTitle}"`;
                }
                else if (item.type === 'book_recommendation') {
                    const note = parsed.note ? `: "${parsed.note}"` : '';
                    displayContent = `đã giới thiệu cuốn sách "${parsed.bookTitle}"${note}`;
                    relatedBookId = parsed.bookId;
                }
                else {
                    displayContent = parsed.text || parsed.message || item.message;
                }
            } catch (e) {
                console.warn("Lỗi parse thông báo:", item.message);
            }
        }

        return {
          ...item,
          status: friend_record?.[0]?.status || item.status, 
          info_sender: senderProfile,
          friend_record: friend_record,
          displayContent: displayContent, // Đã xử lý JSON thành text đẹp
          relatedBookId: relatedBookId
        };
      })
    );

    // 2. Xử lý lời mời CLB
    const processedClubInvites = await Promise.all(
      clubInviteRes.data.map(async (item: any) => {
        const senderProfile = await getProfile(item.sender_id);
        const clubInfo = await getClub(item.club_id);
        return {
          ...item,
          type: 'bookclub_invite',
          info_sender: senderProfile,
          club_name: clubInfo?.name || "Một câu lạc bộ",
        };
      })
    );

    // 3. Xử lý lời mời Buddy Read
    const processedBuddyReadInvites = await Promise.all(
      buddyReadInviteRes.data.map(async (item: any) => {
        const senderProfile = await getProfile(item.sender_id);
        let bookTitle = "một cuốn sách";
        try {
            const brRes = await axios.get(`${BOOK_SERVICE_URL}buddyreads/${item.buddy_read_id}`);
            const bRes = await axios.get(`${BOOK_SERVICE_URL}books/${brRes.data.book_id}`);
            bookTitle = bRes.data.title;
        } catch {}
        return {
          ...item,
          type: 'buddy_read_invite',
          info_sender: senderProfile,
          book_title: bookTitle,
        };
      })
    );

    const allNotifications = [
      ...processedUserNotifs,
      ...processedClubInvites,
      ...processedBuddyReadInvites
    ];
    
    allNotifications.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    notifyList.value = allNotifications;

  } catch (err: any) {
    console.error("Lỗi tải thông báo:", err);
    loi.value = "Không thể tải thông báo.";
  } finally {
    dangTai.value = false;
  }
}

onMounted(async () => {
  if (userInfo.value?.user_id || userInfo.value?.id) {
    await loadNotify(userInfo.value.user_id || userInfo.value.id);
  } else {
    dangTai.value = false;
  }
});
</script>

<template>
  <Navbar />

  <div class="max-w-3xl mx-auto py-10 px-6">
    <div class="flex justify-between items-center mb-6">
        <h1 class="text-2xl font-bold text-teal-700">Thông báo</h1>
        <button @click="loadNotify(userInfo?.user_id)" class="text-sm text-gray-500 hover:text-teal-600 flex items-center gap-1">
            <span>↻</span> Làm mới
        </button>
    </div>

    <div v-if="dangTai" class="text-gray-500 text-center py-10">
      Đang tải thông báo...
    </div>

    <div v-else>
      <div v-if="loi" class="bg-red-50 text-red-600 text-center p-3 rounded mb-3">
        {{ loi }}
      </div>

      <div v-for="tb in notifyList" :key="`${tb.type}-${tb.id}`"
        class="flex items-start gap-4 bg-white p-5 mb-4 border rounded-lg shadow-sm hover:shadow-md transition"
        :class="{'bg-blue-50/30': tb.status === 'unread' || tb.status === 'pending'}"
      >
        <!-- Avatar -->
        <div class="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-lg font-bold text-gray-600 overflow-hidden flex-shrink-0">
          <router-link v-if="tb.info_sender" :to="{ name: 'profile', params: { id: tb.info_sender.user_id } }">
            <img v-if="tb.info_sender.avatar_url" :src="`${AVATAR_SERVER_URL}/${tb.info_sender.avatar_url}`" class="w-full h-full object-cover" />
            <span v-else>{{ tb.info_sender.username?.charAt(0)?.toUpperCase() || "U" }}</span>
          </router-link>
        </div>

        <div class="flex-1">
          <p class="text-gray-800 text-base leading-snug">
            <span class="font-bold text-teal-700 hover:underline cursor-pointer mr-1">
              {{ tb.info_sender?.username || "Ẩn danh" }}
            </span>

            <!-- 1. Lời mời kết bạn -->
            <span v-if="tb.type === 'friend_request'">
              đã gửi lời mời kết bạn.
            </span>

            <!-- 2. Lời mời vào CLB -->
            <span v-else-if="tb.type === 'bookclub_invite'">
              đã mời bạn tham gia câu lạc bộ
              <span class="font-semibold text-yellow-600">{{ tb.club_name || '' }}</span>
            </span>

            <!-- 3. Lời mời Đọc chung -->
            <span v-else-if="tb.type === 'buddy_read_invite'">
              đã mời bạn đọc chung cuốn
              <span class="font-semibold text-yellow-600">{{ tb.book_title || '' }}</span>
            </span>

            <span v-else>
               {{ tb.displayContent }}
            </span>
          </p>

          <p class="text-gray-500 text-xs mt-1.5">
            {{ dinhDangThoiGian(tb.created_at) }}
          </p>

          <!-- Nút Hành Động -->
          <div class="mt-3">
             <!-- Friend Request Actions -->
            <div v-if="tb.type === 'friend_request' && tb.status === 'pending'" class="flex gap-3">
              <button class="px-4 py-1 bg-teal-600 text-white text-sm font-semibold rounded hover:bg-teal-700" @click="acceptFriendRequest(tb.friend_record[0].id)">Chấp nhận</button>
              <button class="px-4 py-1 bg-gray-200 text-gray-700 text-sm font-semibold rounded hover:bg-gray-300" @click="rejectFriendRequest(tb)">Từ chối</button>
            </div>
            <p v-else-if="tb.type === 'friend_request' && tb.status === 'accepted'" class="text-green-600 text-sm font-medium">Đã là bạn bè</p>

            <!-- Book Club Invite Actions -->
            <div v-if="tb.type === 'bookclub_invite' && tb.status === 'pending'" class="flex gap-3">
              <button class="px-4 py-1 bg-teal-600 text-white text-sm font-semibold rounded hover:bg-teal-700" @click="acceptBookClubInvite(tb.id)">Tham gia</button>
              <button class="px-4 py-1 bg-gray-200 text-gray-700 text-sm font-semibold rounded hover:bg-gray-300" @click="rejectBookClubInvite(tb.id)">Từ chối</button>
            </div>

            <!-- Buddy Read Invite Actions -->
            <div v-if="tb.type === 'buddy_read_invite' && tb.status === 'pending'" class="flex gap-3">
              <button class="px-4 py-1 bg-teal-600 text-white text-sm font-semibold rounded hover:bg-teal-700" @click="acceptBuddyReadInvite(tb.id)">Đọc cùng</button>
              <button class="px-4 py-1 bg-gray-200 text-gray-700 text-sm font-semibold rounded hover:bg-gray-300" @click="rejectBuddyReadInvite(tb.id)">Từ chối</button>
            </div>

            <!-- 5. Nút Xem Sách (Cho Book Recommendation) -->
            <div v-if="tb.type === 'book_recommendation' && tb.relatedBookId" class="flex gap-3">
              <router-link :to="`/book/${tb.relatedBookId}`" class="px-4 py-1 bg-indigo-600 text-white text-sm font-semibold rounded hover:bg-indigo-700">
                Xem sách ngay
              </router-link>
            </div>
          </div>
        </div>
        
        <!-- Nút Xóa Thông Báo -->
        <button v-if="(!['friend_request', 'bookclub_invite', 'buddy_read_invite'].includes(tb.type)) || tb.status !== 'pending'" 
                @click="deleteNotification(tb.id)"
                class="text-gray-400 hover:text-red-500 p-1 rounded-full hover:bg-gray-100 transition" 
                title="Xóa thông báo">
            ×
        </button>
      </div>

      <div v-if="notifyList.length === 0 && !loi" class="text-center text-gray-500 py-10 italic">
        Bạn không có thông báo nào.
      </div>
    </div>
  </div>
</template>