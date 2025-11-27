<script setup lang="ts">
import { ref } from "vue";
import axios from "axios";
import { BOOK_SERVICE_URL, USER_SERVICE_URL } from "../../../config";
import { useAuth } from "../../../composables/useAuth";


const props = defineProps<{ clubId: number }>();
const emit = defineEmits(["created", "cancel"]);

const { userInfo } = useAuth();
const title = ref("");
const content = ref("");
const message = ref("");
const loading = ref(false);

async function createDiscussion() {
  const userId = userInfo.value?.id || userInfo.value?.user_id;
  if (!title.value.trim() || !content.value.trim()) {
    message.value = "Vui lòng nhập cả tiêu đề và nội dung.";
    return;
  }
  if (!userId) {
    message.value = "Lỗi xác thực người dùng.";
    return;
  }
  
  loading.value = true;
  try {
    const formData = new FormData();
    formData.append("title", title.value);
    formData.append("content", content.value);
    formData.append("user_id", String(userId));

    const res = await axios.post(
      `${BOOK_SERVICE_URL}bookclubs/${props.clubId}/discussion`, 
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );

    if (res.data && res.data.id) {
        notifyDiscussion(title.value, res.data.id);
    }
    
    emit("created");
    
  } catch (err: any) {
    message.value = err.response?.data?.detail || "Tạo thất bại";
  } finally {
    loading.value = false;
  }
}

async function notifyDiscussion(discussionTitle: string, discussionId: number) {
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}/members`);
    const members = res.data;
    const clubRes = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}`);
    const clubName = clubRes.data.name;
    const currentUserId = userInfo.value?.id || userInfo.value?.user_id;

    for (const member of members) {
        if (member.user_id === currentUserId) continue;
        
        axios.post(`${USER_SERVICE_URL}notifications/add`, {
            receiver_id: member.user_id,
            sender_id: currentUserId,
            type: 'club_discussion',
            message: JSON.stringify({
                title: discussionTitle,
                clubName: clubName,
                discussionId: discussionId
            }),
            status: 'unread'
        }).catch(e => console.error("Lỗi notif discussion:", e));
    }
  } catch (e) { console.error(e); }
}
</script>

<template>
  <div class="p-6 border rounded-lg bg-gray-50">
    <h3 class="text-lg font-semibold mb-4 text-gray-700">Tạo thảo luận mới</h3>
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-600 mb-1">Tiêu đề</label>
        <input v-model="title" type="text" class="w-full border rounded-md px-3 py-2"
          placeholder="Nhập tiêu đề..." />
      </div>
      <div>
        <label class="block text-sm font-medium text-gray-600 mb-1">Nội dung</label>
        <textarea v-model="content" rows="6" class="w-full border rounded-md px-3 py-2"
          placeholder="Viết nội dung thảo luận..."></textarea>
      </div>

      <p v-if="message" class="text-sm text-red-500">{{ message }}</p>

      <div class="flex justify-end space-x-3 mt-4">
        <button @click="$emit('cancel')" class="px-4 py-2 border rounded-md text-gray-600 hover:bg-gray-100">
          Hủy
        </button>
        <button @click="createDiscussion" :disabled="loading"
          class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 rounded-md font-semibold">
          {{ loading ? 'Đang tạo...' : 'Tạo' }}
        </button>
      </div>
    </div>
  </div>
</template>
