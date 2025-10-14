<script setup lang="ts">
import { ref, onMounted } from "vue";
import Navbar from "../components/layout/Navbar.vue";
import { AVATAR_SERVER_URL, USER_SERVICE_URL } from "../config";
import { getProfile } from "../composables/useProfile";
import { useAuth } from "../composables/useAuth";
import axios from "axios";

const { userInfo } = useAuth()

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

async function loadNotify(userId: number) {
  try {
    const respone = await axios.get(`${USER_SERVICE_URL}notifications/user/${userId}`);

    notifyList.value = respone.data;

    const promise = notifyList.value.map((item: any) => getProfile(item.sender_id));

    info_sender.value = await Promise.all(promise);

    notifyList.value = notifyList.value.map((item, index) => ({
      ...item,
      info_sender: info_sender.value[index],
    }));

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
  console.log(notifyList.value[0].info_sender.username);
});


</script>

<template>
  <Navbar />

  <div class="max-w-3xl mx-auto py-10 px-6">
    <h1 class="text-2xl font-bold text-teal-700 mb-4">Thông báo</h1>

    <!-- Loading -->
    <div v-if="dangTai" class="text-gray-500 text-center py-10">
      Đang tải thông báo...
    </div>

    <div v-else>
      <!-- Lỗi -->
      <div
        v-if="loi"
        class="bg-red-50 text-red-600 text-center p-3 rounded mb-3"
      >
        {{ loi }}
      </div>

      <!-- Danh sách thông báo -->
      <h2 class="text-lg font-semibold text-gray-800 mb-4">Mới nhất</h2>

      <div
        v-for="tb in notifyList"
        :key="tb.id"
        class="flex items-start gap-4 bg-white p-5 mb-4 border rounded-lg shadow-sm hover:shadow-md transition"
      >
        <!-- Ảnh đại diện -->
        <div
          class="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-lg font-bold text-gray-600 overflow-hidden"
        >
          <router-link
            v-if="tb.info_sender"
            :to="{ name: 'profile', params: { id: tb.info_sender.user_id } }"
          >
            <div
              class="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center font-bold text-gray-700 overflow-hidden shadow-sm"
            >
              <template v-if="tb.info_sender.avatar_url">
                <img
                  :src="`${AVATAR_SERVER_URL}/${tb.info_sender.avatar_url}`"
                  alt="Avatar người dùng"
                  class="w-full h-full object-cover"
                />
              </template>

              <template v-else>
                {{ tb.info_sender.username?.charAt(0)?.toUpperCase() || "U" }}
              </template>
            </div>
          </router-link>
        </div>

        <!-- Nội dung -->
        <div class="flex-1">
          <p class="text-gray-800 text-base leading-tight">
            <span class="font-semibold text-teal-700 hover:underline cursor-pointer">
              {{ tb.info_sender?.username || "Ẩn danh" }}
            </span>
            {{ " " + tb.message }}
          </p>

          <p class="text-gray-500 text-sm mt-1">
            {{ dinhDangThoiGian(tb.created_at) }}
          </p>

          <p
            v-if="tb.status === 'accepted'"
            class="text-green-600 font-semibold mt-2"
          >
            Đã chấp nhận
          </p>
          <p
            v-else-if="tb.status === 'declined'"
            class="text-red-500 font-semibold mt-2"
          >
            Đã từ chối
          </p>
          <p
            v-else
            class="text-yellow-600 font-semibold mt-2"
          >
            Đang chờ
          </p>
        </div>
      </div>

      <!-- Không có thông báo -->
      <div
        v-if="notifyList.length === 0 && !loi"
        class="text-center text-gray-500 py-10"
      >
        Không có thông báo nào.
      </div>
    </div>
  </div>
</template>

