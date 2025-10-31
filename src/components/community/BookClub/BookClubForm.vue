<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import axios from "axios";
import { BOOK_SERVICE_URL } from "../../../config";
import { useAuth } from "../../../composables/useAuth";

import { BOOKCLUB_IMAGE_SERVER_URL } from "../../../config";

const emit = defineEmits(["saved", "cancel"]);

const router = useRouter(); 

const props = defineProps({
  clubId: {
    type: Number,
    default: null,
  },
});

const { loadUserFromToken } = useAuth();

const loading = ref(false);
const isDeleting = ref(false); 
const message = ref("");

const form = ref({
  name: "",
  description: "",
  rules: "",
  avatar: null as File | null,
  avatar_url: "",
});

async function loadClubInfo() {
  if (!props.clubId) return;

  loading.value = true;
  try {
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}`);
    const club = res.data;
    form.value.name = club.name;
    form.value.description = club.description || "";
    form.value.rules = club.rules || "";
    form.value.avatar_url = club.avatar_url || "";
  } catch (err: any) {
    message.value = err.response?.data?.detail || "Không thể tải thông tin câu lạc bộ!";
  } finally {
    loading.value = false;
  }
}

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement | null;
  const file = input?.files?.[0] ?? null;
  form.value.avatar = file;

  if (file) {
    if (form.value.avatar_url) URL.revokeObjectURL(form.value.avatar_url);
    form.value.avatar_url = URL.createObjectURL(file);
  }
}

onUnmounted(() => {
  if (form.value.avatar_url && form.value.avatar_url.startsWith("blob:"))
    URL.revokeObjectURL(form.value.avatar_url);
});

async function saveClub() {
  if (!form.value.name.trim()) {
    message.value = "Vui lòng nhập tên câu lạc bộ!";
    return;
  }

  loading.value = true;
  message.value = "";

  const token = localStorage.getItem("token");
  if (!token) {
    message.value = "Vui lòng đăng nhập!";
    loading.value = false;
    return;
  }

  const formData = new FormData();
  formData.append("name", form.value.name);
  formData.append("description", form.value.description);
  formData.append("rules", form.value.rules);
  if (form.value.avatar) formData.append("file", form.value.avatar);

  try {
    let res;

    if (props.clubId) {
      res = await axios.put(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`,
        },
      });
    } else {
      const decoded = loadUserFromToken();
      const creatorId = decoded?.id || decoded?.user_id;
      formData.append("creator_id", String(creatorId));

      res = await axios.post(`${BOOK_SERVICE_URL}bookclubs/create`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
          Authorization: `Bearer ${token}`,
        },
      });
    }

    emit("saved", res.data);
    message.value = props.clubId ? "Cập nhật thành công!" : "Tạo mới thành công!";
  } catch (err: any) {
    message.value = err.response?.data?.detail || "Đã xảy ra lỗi!";
  } finally {
    loading.value = false;
  }
}

async function deleteClub() {
  if (!props.clubId) return;

  if (!confirm("Bạn có chắc chắn muốn xóa câu lạc bộ này không? Mọi dữ liệu liên quan (thảo luận, thành viên...) sẽ bị mất vĩnh viễn.")) {
    return;
  }

  isDeleting.value = true;
  message.value = "";
  const token = localStorage.getItem("token");

  if (!token) {
    message.value = "Vui lòng đăng nhập!";
    isDeleting.value = false;
    return;
  }

  try {
    await axios.delete(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    message.value = "Đã xóa câu lạc bộ thành công!";
    router.push("/community");
  } catch (err: any) {
    message.value = err.response?.data?.detail || "Đã xảy ra lỗi khi xóa!";
  } finally {
    isDeleting.value = false;
  }
}

onMounted(() => {
  loadClubInfo();
});
</script>

<template>
  <div class="bg-white rounded-lg shadow p-6 text-gray-700 max-w-3xl mx-auto">
    <h3 class="text-lg font-semibold text-yellow-500 mb-4">
      {{ props.clubId ? "Chỉnh sửa câu lạc bộ" : "Tạo câu lạc bộ mới" }}
    </h3>

    <div class="space-y-4">
      <div>
        <label class="block font-medium mb-1">Tên câu lạc bộ *</label>
        <input v-model="form.name" type="text"
          class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none" />
      </div>

      <div>
        <label class="block font-medium mb-1">Ảnh đại diện</label>
        <input type="file" accept="image/*" @change="onFileChange"
          class="w-full border border-gray-300 rounded-md p-2" />
        <div v-if="form.avatar_url" class="mt-3">
          <img :src="form.avatar_url.startsWith('blob:')
            ? form.avatar_url
            : `${BOOKCLUB_IMAGE_SERVER_URL}/${form.avatar_url}`" class="w-32 h-32 object-cover rounded-md" />
        </div>

      </div>

      <div>
        <label class="block font-medium mb-1">Mô tả</label>
        <textarea v-model="form.description" rows="3"
          class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"></textarea>
      </div>

      <div>
        <label class="block font-medium mb-1">Nội quy</label>
        <textarea v-model="form.rules" rows="3"
          class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"></textarea>
      </div>

      <p v-if="message" class="text-sm text-red-500">{{ message }}</p>

      <div class="flex justify-between items-center mt-4">
        <button v-if="props.clubId" @click="deleteClub" :disabled="loading || isDeleting"
          class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-md">
          {{ isDeleting ? "Đang xóa..." : "Xóa câu lạc bộ" }}
        </button>

        <div v-else></div>

        <div class="flex justify-end gap-3">
          <button @click="$emit('cancel')" :disabled="loading || isDeleting"
            class="px-4 py-2 border border-gray-400 rounded-md text-gray-600 hover:bg-gray-100">
            Hủy
          </button>
          <button @click="saveClub" :disabled="loading || isDeleting"
            class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md">
            {{ loading ? "Đang lưu..." : props.clubId ? "Lưu thay đổi" : "Tạo mới" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>