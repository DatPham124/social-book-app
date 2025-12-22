<script setup lang="ts">
import { ref } from "vue";
import axios from "axios";
import { BOOK_SERVICE_URL } from "../../config.ts";

const props = defineProps<{
  book: any;
  userId: number;
}>();

const emit = defineEmits(["update"]);
const isSaving = ref(false);

async function updateReadingProgress(newPage: number) {
  isSaving.value = true;
  try {
    const payload = {
        current_page: newPage
    };

    await axios.put(
      `${BOOK_SERVICE_URL}books/reading-progress/${props.userId}/${props.book.id}`,
      payload
    );

    props.book.current_page = newPage;
    props.book.progress_percentage =
      props.book.total_pages > 0
        ? Math.round((newPage / props.book.total_pages) * 100)
        : 0;
    
    props.book.editingProgress = false;

    emit("update", props.book);
  } catch (error: any) {
    alert(error.response?.data?.detail || "Lỗi khi cập nhật tiến độ");
  } finally {
    isSaving.value = false;
  }
}
</script>

<template>
  <div>
    <div class="flex justify-between items-center text-sm text-gray-600 mb-1">
      <span>Tiến độ: {{ book.current_page }}/{{ book.total_pages }} trang</span>
      <div class="flex items-center gap-2">
        <span class="font-semibold text-yellow-600 pl-2">
          {{ book.progress_percentage }}%
        </span>
        <button
          @click="book.editingProgress = !book.editingProgress"
          class="text-gray-400 hover:text-yellow-600 transition-colors p-1"
          title="Cập nhật tiến độ"
        >
          ✏️
        </button>
      </div>
    </div>

    <div class="w-full bg-gray-200 rounded-full h-2.5">
      <div
        class="bg-yellow-400 h-2.5 rounded-full transition-all duration-500"
        :style="{ width: `${book.progress_percentage}%` }"
      ></div>
    </div>

    <div v-if="book.editingProgress" class="mt-2 flex gap-2">
      <input
        type="number"
        v-model.number="book.newPage"
        min="0"
        :max="book.total_pages"
        class="w-20 border rounded px-2 py-1 text-sm outline-none focus:border-yellow-500"
        placeholder="Số trang"
      />
      <button
        @click="updateReadingProgress(book.newPage)"
        class="px-2 py-1 bg-yellow-400 text-white rounded text-sm hover:bg-yellow-500 disabled:opacity-50"
        :disabled="isSaving"
      >
        <span v-if="isSaving">Lưu...</span>
        <span v-else>Lưu</span>
      </button>
    </div>
  </div>
</template>