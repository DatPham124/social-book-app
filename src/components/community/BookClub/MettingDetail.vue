<script setup lang="ts">
import { Ref, ref } from "vue";
import { useBookSearch } from "../../../composables/useBookSearch";
import { BOOK_SERVICE_URL } from "../../../config";
import axios from "axios";
import { useAuth } from "../../../composables/useAuth"; 

const props = defineProps<{ clubId: number }>();
const emit = defineEmits(["created", "cancel"]);

const title = ref("");
const date = ref("");
const time = ref("");
const selectedBook = ref<Book | null>(null);

const { userInfo } = useAuth(); 

interface Book {
  id: number;
  title: string;
  author?: string;
  cover_url?: string;
}

const { query, results, searchBooks } = useBookSearch() as {
  query: Ref<string>;
  results: Ref<Book[]>;
  searchBooks: () => Promise<void>;
};

function handleSelectBook(book: Book) {
  selectedBook.value = book;
  query.value = book.title;
  results.value = [];
}

// 3. SỬA HÀM createMeeting
async function createMeeting() {
  // Lấy user_id từ userInfo
  const userId = userInfo.value?.id || userInfo.value?.user_id;

  if (!title.value || !date.value || !time.value) {
    // Sửa lại câu alert cho đúng
    alert("Vui lòng điền tên, ngày và giờ họp!");
    return;
  }

  // Thêm kiểm tra user_id
  if (!userId) {
    alert("Lỗi: Không thể xác thực người dùng. Vui lòng đăng nhập lại.");
    return;
  }

  try {
    const datetimeLocal = `${date.value}T${time.value}:00`;
    const formData = new FormData();
    formData.append("title", title.value);
    formData.append("date", datetimeLocal);
    formData.append("user_id", String(userId)); // <-- GỬI user_id LÊN BACKEND

    if (selectedBook.value) {
      formData.append("book_id", String(selectedBook.value.id));
    }
    
    await axios.post(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}/meetings`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    alert("Tạo cuộc họp thành công!");
    emit("created");
  } catch (error: any) { // Thêm kiểu 'any'
    console.error("Lỗi khi tạo cuộc họp:", error);
    // Hiển thị lỗi từ backend nếu có
    alert(error.response?.data?.detail || "Tạo cuộc họp thất bại, vui lòng thử lại!");
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

      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">Ngày họp</label>
          <input v-model="date" type="date" class="w-full border rounded-md px-3 py-2" />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-1">Giờ họp</label>
          <input v-model="time" type="time" class="w-full border rounded-md px-3 py-2" />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-600 mb-1">Chọn sách (Không bắt buộc)</label>
        <input v-model="query" @input="searchBooks" type="text" class="w-full border rounded-md px-3 py-2"
          placeholder="Nhập tên sách để tìm..." />

        <ul v-if="results.length" class="border rounded-md mt-2 bg-white shadow-sm max-h-48 overflow-y-auto">
          <li v-for="book in results" :key="book.id" @click="handleSelectBook(book)"
            class="px-3 py-2 hover:bg-yellow-50 cursor-pointer">
            {{ book.title }}
          </li>
        </ul>

        <p v-if="selectedBook" class="mt-2 text-sm text-gray-700">
          📚 Đã chọn: <strong>{{ selectedBook.title }}</strong>
        </p>
      </div>

      <div class="flex justify-end space-x-3 mt-6">
        <button @click="$emit('cancel')" class="px-4 py-2 border rounded-md text-gray-600 hover:bg-gray-100">
          Hủy
        </button>
        <button @click="createMeeting" class="px-4 py-2 bg-yellow-400 hover:bg-yellow-500 rounded-md font-semibold">
          Tạo
        </button>
      </div>
    </div>
  </div>
</template>
