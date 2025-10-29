<script setup lang="ts">
import { ref, onUnmounted } from "vue"
import axios from "axios"
import { BOOK_SERVICE_URL } from "../../../config"   
import { useAuth } from "../../../composables/useAuth"  

const emit = defineEmits(["created", "cancel"])

const { userInfo, loadUserFromToken } = useAuth()

const loading = ref(false)
const message = ref("")

const newClub = ref({
  name: "",
  description: "",
  rules: "",
  avatar: null as File | null,
  avatar_url: "",
})

function onFileChange(e: Event) {
  const input = e.target as HTMLInputElement | null
  const file = input?.files?.[0] ?? null
  newClub.value.avatar = file

  if (file) {
    if (newClub.value.avatar_url) URL.revokeObjectURL(newClub.value.avatar_url)
    newClub.value.avatar_url = URL.createObjectURL(file)
  } else {
    if (newClub.value.avatar_url) URL.revokeObjectURL(newClub.value.avatar_url)
    newClub.value.avatar_url = ""
  }
}

onUnmounted(() => {
  if (newClub.value.avatar_url) URL.revokeObjectURL(newClub.value.avatar_url)
})

async function createClub() {
  if (!newClub.value.name.trim()) {
    message.value = "Vui lòng nhập tên câu lạc bộ!"
    return
  }

  const token = localStorage.getItem("token")
  if (!token) {
    message.value = "Vui lòng đăng nhập để tạo câu lạc bộ!"
    return
  }

  const decoded = loadUserFromToken()
  const creatorId = decoded?.id || decoded?.user_id
  if (!creatorId) {
    message.value = "Không xác định được người tạo!"
    return
  }

  loading.value = true
  message.value = ""

  try {
    const formData = new FormData()
    formData.append("name", newClub.value.name)
    formData.append("creator_id", String(creatorId)) 
    formData.append("description", newClub.value.description || "")
    if (newClub.value.avatar) formData.append("file", newClub.value.avatar)

    const res = await axios.post(`${BOOK_SERVICE_URL}bookclubs/create`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
        "Authorization": `Bearer ${token}`,
      },
    })

    const createdClub = res.data.club || res.data
    message.value = "Tạo câu lạc bộ thành công!"
    emit("created", createdClub)
  } catch (err: any) {
    console.error("Lỗi khi tạo CLB:", err)
    message.value = err.response?.data?.detail || "Lỗi khi tạo câu lạc bộ!"
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="bg-white rounded-lg shadow p-6 text-gray-700 max-w-3xl mx-auto">
    <h3 class="text-lg font-semibold text-yellow-500 mb-4">Tạo câu lạc bộ mới</h3>

    <div class="space-y-4">
      <!-- Tên CLB -->
      <div>
        <label class="block font-medium mb-1">Tên câu lạc bộ *</label>
        <input
          v-model="newClub.name"
          type="text"
          class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
          placeholder="Nhập tên câu lạc bộ..."
        />
      </div>

      <div>
        <label class="block font-medium mb-1">Ảnh đại diện (tùy chọn)</label>
        <input
          type="file"
          accept="image/*"
          @change="onFileChange"
          class="w-full border border-gray-300 rounded-md p-2"
        />
        <div v-if="newClub.avatar_url" class="mt-3">
          <img :src="newClub.avatar_url" alt="Ảnh xem trước" class="w-32 h-32 object-cover rounded-md" />
        </div>
      </div>

      <div>
        <label class="block font-medium mb-1">Mô tả</label>
        <textarea
          v-model="newClub.description"
          rows="3"
          class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
          placeholder="Giới thiệu ngắn gọn về câu lạc bộ..."
        ></textarea>
      </div>

      <div>
        <label class="block font-medium mb-1">Nội quy (tùy chọn)</label>
        <textarea
          v-model="newClub.rules"
          rows="3"
          class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
          placeholder="Đặt ra vài quy tắc hoặc hướng dẫn cho thành viên..."
        ></textarea>
      </div>

      <p v-if="message" class="text-sm text-red-500">{{ message }}</p>

      <div class="flex justify-end gap-3 mt-4">
        <button
          @click="$emit('cancel')"
          class="px-4 py-2 border border-gray-400 rounded-md text-gray-600 hover:bg-gray-100 transition-colors"
        >
          Hủy
        </button>
        <button
          @click="createClub"
          :disabled="loading"
          class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md transition-colors"
        >
          <span v-if="loading">Đang tạo...</span>
          <span v-else>Tạo câu lạc bộ</span>
        </button>
      </div>
    </div>
  </div>
</template>
