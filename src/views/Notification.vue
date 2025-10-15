<script setup lang="ts">
import { ref, onMounted } from "vue";
import Navbar from "../components/layout/Navbar.vue";
import { AVATAR_SERVER_URL, USER_SERVICE_URL } from "../config";
import { getProfile } from "../composables/useProfile";
import { useAuth } from "../composables/useAuth";
import axios from "axios";

const { userInfo } = useAuth();

const friendID = ref<number | null>(null);
const notifyList = ref<any[]>([]);
const info_sender = ref<any[]>([]);
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

async function rejectFriendRequest(tb: any) {
  try {
    await axios.delete(`${USER_SERVICE_URL}friends/delete/${tb.message}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    notifyList.value = notifyList.value.filter((n) => n.id !== tb.id);
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

    // Tìm thông báo tương ứng
    const index = notifyList.value.findIndex(
      (tb) => tb.message == String(friendId)
    );
    if (index !== -1) {
      // Cập nhật trạng thái bạn bè
      if (notifyList.value[index].friend_record?.[0]) {
        notifyList.value[index].friend_record[0].status = "accepted";
      }
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

async function loadNotify(userId: number) {
  try {
    const respone = await axios.get(`${USER_SERVICE_URL}notifications/user/${userId}`);
    notifyList.value = respone.data;

    const promise = notifyList.value.map((item: any) => getProfile(item.sender_id));
    info_sender.value = await Promise.all(promise);

    const friendPromises = notifyList.value.map((item: any) => {
      const fid = Number(item.message);
      return checkFriendStatus(fid);
    });
    const friendsInfo = await Promise.all(friendPromises);

    notifyList.value = notifyList.value.map((item, index) => ({
      ...item,
      info_sender: info_sender.value[index],
      friend_record: friendsInfo[index],
    }));

    console.log(notifyList.value)


  } catch (err: any) {
    console.error("Lỗi tải thông báo:", err);
    loi.value = err.message;
    notifyList.value = [];
  } finally {
    dangTai.value = false;
  }
}

onMounted(async () => {
  await loadNotify(userInfo.value.user_id);
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

      <div v-for="tb in notifyList" :key="tb.id"
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

            <span v-if="tb.type === 'friend_request'">
              đã gửi lời mời kết bạn
            </span>
          </p>

          <p class="text-gray-500 text-sm mt-1">
            {{ dinhDangThoiGian(tb.created_at) }}
          </p>

          <!-- Khi lời mời đang chờ -->
          <div class="mt-3 flex gap-3" v-if="tb.friend_record?.[0]?.status === 'pending'">
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

          <!-- Khi đã chấp nhận -->
          <p v-else-if="tb.friend_record?.[0]?.status === 'accepted'" class="text-green-600 font-semibold mt-2">
            Đã chấp nhận lời mời
          </p>


          <p v-else-if="!tb.friend_record" class="text-gray-500 mt-2">
            Lời mời không còn hợp lệ
          </p>
        </div>

      </div>

      <div v-if="notifyList.length === 0 && !loi" class="text-center text-gray-500 py-10">
        Không có thông báo nào.
      </div>
    </div>
  </div>
</template>
