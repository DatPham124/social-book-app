<script setup lang="ts">
import { ref, onMounted } from "vue";
import Navbar from "../components/layout/Navbar.vue";
// Thêm BOOK_SERVICE_URL
import { AVATAR_SERVER_URL, USER_SERVICE_URL, BOOK_SERVICE_URL } from "../config";
import { getProfile } from "../composables/useProfile";
import { useAuth } from "../composables/useAuth";
import axios from "axios";

const { userInfo } = useAuth();

const notifyList = ref<any[]>([]);
const info_sender = ref<any[]>([]); // (Giữ lại, nhưng logic mới sẽ không dùng)
const dangTai = ref(true);
const loi = ref<string | null>(null);

function dinhDangThoiGian(thoiGianStr: string) {
  const diffMs = Date.now() - new Date(thoiGianStr).getTime();
  const phut = Math.floor(diffMs / 60000);
  if (phut < 1) return "vừa xong";
  if (phut < 60) return `${phut} phút trước`;
  const gio = Math.floor(phut / 60);
  if (gio < 24) return `${gio} giờ trước`;
  const ngay = Math.floor(gio / 24);
  return `${ngay} ngày trước`;
}

const token = localStorage.getItem("token");

// (Các hàm friend request giữ nguyên)
async function rejectFriendRequest(tb: any) {
  try {
    await axios.delete(`${USER_SERVICE_URL}friends/delete/${tb.message}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    // Xóa thông báo khỏi user-service
    await deleteNotification(tb.id);
  } catch (err: any) {
    console.error("Lỗi khi từ chối lời mời:", err);
    alert("Không thể từ chối lời mời. Vui lòng thử lại sau.");
  }
}

async function acceptFriendRequest(friendId: number) {
  try {
    const response = await axios.put(
      `${USER_SERVICE_URL}friends/update/${friendId}?status=accepted`,
      {},
      {
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    const index = notifyList.value.findIndex(
      (tb) => tb.message == String(friendId) && tb.type === 'friend_request'
    );
    if (index !== -1) {
      if (notifyList.value[index].friend_record?.[0]) {
        notifyList.value[index].friend_record[0].status = "accepted";
      }
      // Đánh dấu đã chấp nhận ở frontend
      notifyList.value[index].status = 'accepted';
    }
    console.log("Chấp nhận lời mời kết bạn thành công:", response.data);
  } catch (err: any) {
    console.error("Lỗi khi chấp nhận lời mời:", err);
    loi.value = err.message || "Có lỗi xảy ra khi chấp nhận kết bạn";
  }
}

async function checkFriendStatus(friendId?: number) {
  if (!token || !userInfo || !friendId) return null;
  try {
    const response = await axios.get(`${USER_SERVICE_URL}friends/${friendId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  } catch (error) {
    console.error("Không thể kiểm tra trạng thái bạn bè:", error);
    return null;
  }
}

// --- HÀM MỚI CHO BOOK CLUB (THEO LOGIC ĐƠN GIẢN) ---
async function getClub(clubId: number) {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${clubId}`);
    return res.data;
  } catch (error) {
    console.error("Lỗi khi lấy thông tin câu lạc bộ:", error);
    return null;
  }
}

async function acceptBookClubInvite(invitationId: number) {
  try {
    // 1. Gọi API "Accept" mới của book-service
    await axios.post(
      `${BOOK_SERVICE_URL}bookclubs/invitations/${invitationId}/accept`
    );

    // 2. Cập nhật UI: Xóa lời mời khỏi danh sách
    notifyList.value = notifyList.value.filter(n => !(n.id === invitationId && n.type === 'bookclub_invite'));
  } catch (err: any) {
    console.error("Lỗi khi chấp nhận lời mời club:", err);
    loi.value = err.response?.data?.detail || "Lỗi khi tham gia club";
  }
}

async function rejectBookClubInvite(invitationId: number) {
  try {
    // 1. Gọi API "Decline" mới của book-service
    await axios.delete(
      `${BOOK_SERVICE_URL}bookclubs/invitations/${invitationId}/decline`
    );

    // 2. Cập nhật UI: Xóa lời mời khỏi danh sách
    notifyList.value = notifyList.value.filter(n => !(n.id === invitationId && n.type === 'bookclub_invite'));
  } catch (err) {
    console.error("Lỗi khi từ chối lời mời club:", err);
  }
}

async function deleteNotification(notificationId: number) {
  // Hàm này chỉ dùng để xóa thông báo KẾT BẠN
  try {
    await axios.delete(`${USER_SERVICE_URL}notifications/${notificationId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    notifyList.value = notifyList.value.filter(n => !(n.id === notificationId && n.type === 'friend_request'));
  } catch (err) {
    console.error("Lỗi khi xóa thông báo:", err);
  }
}
// --- KẾT THÚC HÀM MỚI ---


// --- VIẾT LẠI HÀM LOADNOTIFY ---
async function loadNotify(userId: number) {
  try {
    // 1. Tạo 2 promise để gọi 2 service cùng lúc
    const friendNotifyPromise = axios.get(`${USER_SERVICE_URL}notifications/user/${userId}`);
    const clubInvitePromise = axios.get(`${BOOK_SERVICE_URL}bookclubs/invitations/${userId}`);

    const [friendNotifyRes, clubInviteRes] = await Promise.all([
      friendNotifyPromise,
      clubInvitePromise
    ]);

    const friendRequests = friendNotifyRes.data;
    const clubInvites = clubInviteRes.data;

    // 2. Xử lý lời mời kết bạn (Logic cũ)
    const processedFriendRequests = await Promise.all(
      friendRequests.map(async (item: any) => {
        const senderProfile = await getProfile(item.sender_id);
        let friend_record = null;
        if (item.type === 'friend_request') {
          const fid = Number(item.message);
          friend_record = await checkFriendStatus(fid);
        }
        return {
          ...item,
          status: friend_record?.[0]?.status || 'pending',
          info_sender: senderProfile,
          friend_record: friend_record,
        };
      })
    );

    // 3. Xử lý lời mời vào CLB (Logic mới)
    const processedClubInvites = await Promise.all(
      clubInvites.map(async (item: any) => {
        const senderProfile = await getProfile(item.sender_id);
        const clubInfo = await getClub(item.club_id);
        return {
          ...item,
          type: 'bookclub_invite', // Gán type thủ công
          info_sender: senderProfile,
          club_name: clubInfo?.name || "Một câu lạc bộ",
          // status: 'pending' (đã có sẵn từ item)
        };
      })
    );

    // 4. Gộp 2 danh sách và sắp xếp theo ngày
    const allNotifications = [...processedFriendRequests, ...processedClubInvites];
    allNotifications.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    notifyList.value = allNotifications;

  } catch (err: any) {
    console.error("Lỗi tải thông báo:", err);
    loi.value = err.message;
    notifyList.value = [];
  } finally {
    dangTai.value = false;
  }
}

onMounted(async () => {
  if (userInfo.value?.user_id || userInfo.value?.id) {
    await loadNotify(userInfo.value.user_id || userInfo.value.id);
  } else {
    loi.value = "Không thể xác thực người dùng.";
    dangTai.value = false;
  }
});
</script>

<template>
  <Navbar />

  <div class="max-w-3xl mx-auto py-10 px-6">
    <h1 class="text-2xl font-bold text-teal-700 mb-4">Thông báo</h1>

    <div v-if="dangTai" class="text-gray-500 text-center py-10">
      Đang tải thông báo...
    </div>

    <div v-else>
      <div v-if="loi" class="bg-red-50 text-red-600 text-center p-3 rounded mb-3">
        {{ loi }}
      </div>

      <h2 class="text-lg font-semibold text-gray-800 mb-4">Mới nhất</h2>

      <div v-for="tb in notifyList" :key="`${tb.type}-${tb.id}`"
        class="flex items-start gap-4 bg-white p-5 mb-4 border rounded-lg shadow-sm hover:shadow-md transition">
        <div
          class="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-lg font-bold text-gray-600 overflow-hidden">
          <router-link v-if="tb.info_sender" :to="{ name: 'profile', params: { id: tb.info_sender.user_id } }">
            <div
              class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm">
              <template v-if="tb.info_sender.avatar_url">
                <img :src="`${AVATAR_SERVER_URL}/${tb.info_sender.avatar_url}`" alt="Avatar người dùng"
                  class="w-full h-full object-cover" />
              </template>
              <template v-else>
                {{ tb.info_sender.username?.charAt(0)?.toUpperCase() || "U" }}
              </template>
            </div>
          </router-link>
        </div>

        <div class="flex-1">
          <p class="text-gray-800 text-base leading-tight">
            <span class="font-semibold text-teal-700 hover:underline cursor-pointer">
              {{ tb.info_sender?.username || "Ẩn danh" }}
            </span>

            <!-- Lời mời kết bạn -->
            <span v-if="tb.type === 'friend_request'">
              đã gửi lời mời kết bạn
            </span>
            
            <!-- Lời mời vào CLB -->
            <span v-else-if="tb.type === 'bookclub_invite'">
              đã mời bạn tham gia câu lạc bộ
              <span class="font-semibold text-yellow-600">{{ tb.club_name || '' }}</span>
            </span>
          </p>

          <p class="text-gray-500 text-sm mt-1">
            {{ dinhDangThoiGian(tb.created_at) }}
          </p>

          <!-- Nút bấm cho Lời mời kết bạn -->
          <!-- SỬA LỖI TYPO: vt-if -> v-if -->
          <div v-if="tb.type === 'friend_request'">
            <div class="mt-3 flex gap-3" v-if="tb.status === 'pending'">
              <button class="px-4 py-1 border border-teal-600 text-teal-600 font-semibold rounded-md
                hover:bg-teal-600 hover:text-white transition-colors duration-200"
                @click="acceptFriendRequest(tb.friend_record[0].id)">
                Chấp nhận
              </button>

              <button class="px-4 py-1 border border-gray-300 text-gray-800 font-semibold rounded-md
                hover:bg-rose-500 hover:text-white hover:border-rose-500 transition-colors duration-200"
                @click="rejectFriendRequest(tb)">
                Từ chối
              </button>
            </div>
            <p v-else-if="tb.status === 'accepted'" class="text-green-600 font-semibold mt-2">
              Đã chấp nhận lời mời
            </p>
            <p v-else-if="!tb.friend_record" class="text-gray-500 mt-2">
              Lời mời không còn hợp lệ
            </p>
          </div>

          <!-- Nút bấm cho Lời mời vào CLB -->
          <div v-else-if="tb.type === 'bookclub_invite'">
            <div class="mt-3 flex gap-3" v-if="tb.status === 'pending'">
              <button class="px-4 py-1 border border-teal-600 text-teal-600 font-semibold rounded-md
                hover:bg-teal-600 hover:text-white transition-colors duration-200"
                @click="acceptBookClubInvite(tb.id)">
                Chấp nhận
              </button>

              <button class="px-4 py-1 border border-gray-300 text-gray-800 font-semibold rounded-md
                hover:bg-rose-500 hover:text-white hover:border-rose-500 transition-colors duration-200"
                @click="rejectBookClubInvite(tb.id)">
                Từ chối
              </button>
            </div>
          </div>

        </div>

      </div>

      <div v-if="notifyList.length === 0 && !loi" class="text-center text-gray-500 py-10">
        Không có thông báo nào.
      </div>
    </div>
  </div>
</template>

