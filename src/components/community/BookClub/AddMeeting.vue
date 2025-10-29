<script setup lang="ts">
import { Ref, ref } from "vue";
import { useBookSearch } from "../../../composables/useBookSearch";
import { BOOK_SERVICE_URL } from "../../../config";
import axios from "axios";

const props = defineProps<{
    clubId: number;
}>();

const emit = defineEmits(["created", "cancel"]);

const title = ref("");
const date = ref("");
const selectedBook = ref<Book | null>(null);

interface Book {
    id: number
    title: string
    author?: string
    cover_url?: string
}


const { query, results, searchBooks } = useBookSearch() as {
    query: Ref<string>
    results: Ref<Book[]>
    searchBooks: () => Promise<void>
};
function handleSelectBook(book: Book) {
    selectedBook.value = book;
    query.value = book.title;
    results.value = [];
}

async function createMeeting() {
  if (!title.value || !date.value || !selectedBook.value) {
    alert("Vui lòng điền đầy đủ thông tin và chọn sách!");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("title", title.value);
    formData.append("date", date.value);

    // Gọi API backend
    await axios.post(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}/meetings`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    alert("Tạo cuộc họp thành công!");
    emit("created");
  } catch (error) {
    console.error("Lỗi khi tạo cuộc họp:", error);
    alert("Tạo cuộc họp thất bại, vui lòng thử lại!");
  }
}
</script>

<template>
    <div class="p-6 border rounded-lg bg-gray-50">
        <h3 class="text-lg font-semibold mb-4 text-gray-700">Tạo cuộc họp mới</h3>

        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-600 mb-1">Tên cuộc họp</label>
                <input v-model="title" type="text" class="w-full border rounded-md px-3 py-2"
                    placeholder="Nhập tiêu đề cuộc họp" />
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-600 mb-1">Ngày họp</label>
                <input v-model="date" type="date" class="w-full border rounded-md px-3 py-2" />
            </div>

            <div>
                <label class="block text-sm font-medium text-gray-600 mb-1">Chọn sách</label>
                <input v-model="query" @input="searchBooks" type="text" class="w-full border rounded-md px-3 py-2"
                    placeholder="Nhập tên sách để tìm..." />

                <!-- Danh sách gợi ý -->
                <ul v-if="results.length" class="border rounded-md mt-2 bg-white shadow-sm max-h-48 overflow-y-auto">
                    <li v-for="book in results" :key="book.id" @click="handleSelectBook(book)"
                        class="px-3 py-2 hover:bg-yellow-50 cursor-pointer">
                        {{ book.title }}
                    </li>
                </ul>

                <!-- Sách đã chọn -->
                <p v-if="selectedBook" class="mt-2 text-sm text-gray-700">
                    📚 Đã chọn: <strong>{{ selectedBook.title }}</strong>
                </p>
            </div>

            <div class="flex justify-end space-x-3 mt-6">
                <button @click="$emit('cancel')" class="px-4 py-2 border rounded-md text-gray-600 hover:bg-gray-100">
                    Hủy
                </button>
                <button @click="createMeeting"
                    class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 rounded-md font-semibold">
                    Tạo
                </button>
            </div>
        </div>
    </div>
</template>
