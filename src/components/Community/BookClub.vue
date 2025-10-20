<script setup lang="ts">
import { ref } from 'vue'

// trạng thái xem có câu lạc bộ hay chưa
const hasClub = ref(false)
const creatingClub = ref(false)

// dữ liệu của form tạo câu lạc bộ
const newClub = ref({
  name: '',
  description: '',
  rules: '',
  avatar: null as File | null,
})

function startCreateClub() {
  creatingClub.value = true
}

function cancelCreate() {
  creatingClub.value = false
}

function createClub() {
  console.log("✅ Tạo câu lạc bộ:", newClub.value)
  hasClub.value = true
  creatingClub.value = false
}
</script>

<template>
  <div class="mt-8 bg-white rounded-lg shadow p-6 text-gray-700">

    <!-- ✅ Nếu chưa có câu lạc bộ -->
    <div v-if="!hasClub && !creatingClub" class="text-center py-10">
      <p class="italic text-gray-500 mb-6">Bạn chưa tham gia câu lạc bộ sách nào!</p>
      <button
        @click="startCreateClub"
        class="flex items-center gap-2 mx-auto bg-yellow-400 hover:bg-yellow-500 text-black font-semibold px-4 py-2 rounded-md transition-colors"
      >
        <span>➕ Tạo câu lạc bộ mới</span>
      </button>
    </div>

    <!-- ✅ Form tạo câu lạc bộ -->
    <div v-else-if="creatingClub">
      <h3 class="text-lg font-semibold text-yellow-500 mb-4">Tạo câu lạc bộ mới</h3>

      <div class="space-y-4">
        <!-- Tên -->
        <div>
          <label class="block font-medium mb-1">Tên câu lạc bộ</label>
          <input
            v-model="newClub.name"
            type="text"
            class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
            placeholder="Nhập tên câu lạc bộ..."
          />
        </div>

        <!-- Ảnh -->
        <div>
          <label class="block font-medium mb-1">Ảnh đại diện (tùy chọn)</label>
          <input
            type="file"
            accept="image/*"
            @change="(e: any) => newClub.avatar = e.target.files[0]"
            class="w-full border border-gray-300 rounded-md p-2"
          />
        </div>

        <!-- Mô tả -->
        <div>
          <label class="block font-medium mb-1">Mô tả</label>
          <textarea
            v-model="newClub.description"
            rows="3"
            class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
            placeholder="Giới thiệu ngắn gọn về câu lạc bộ..."
          ></textarea>
        </div>

        <!-- Quy định -->
        <div>
          <label class="block font-medium mb-1">Nội quy (tùy chọn)</label>
          <textarea
            v-model="newClub.rules"
            rows="3"
            class="w-full border border-gray-300 rounded-md p-2 focus:ring-2 focus:ring-yellow-400 focus:outline-none"
            placeholder="Đặt ra vài quy tắc hoặc hướng dẫn cho thành viên..."
          ></textarea>
        </div>

        <!-- Nút hành động -->
        <div class="flex justify-end gap-3 mt-4">
          <button
            @click="cancelCreate"
            class="px-4 py-2 border border-gray-400 rounded-md text-gray-600 hover:bg-gray-100 transition-colors"
          >
            Hủy
          </button>
          <button
            @click="createClub"
            class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 text-black font-semibold rounded-md transition-colors"
          >
            Tạo câu lạc bộ
          </button>
        </div>
      </div>
    </div>

    <!-- ✅ Sau khi đã tạo -->
    <div v-else class="text-center py-10">
      <p class="text-gray-600">🎉 Bạn đã tạo câu lạc bộ <strong>{{ newClub.name }}</strong>!</p>
      <p class="text-gray-400 mt-2">Bạn có thể thêm thành viên hoặc chỉnh sửa sau.</p>
    </div>
  </div>
</template>
