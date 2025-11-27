<script setup lang="ts">
import { Ref, ref } from "vue";
import { useBookSearch } from "../../../composables/useBookSearch";
import { BOOK_SERVICE_URL } from "../../../config";
import axios from "axios";
import { useAuth } from "../../../composables/useAuth";
import { USER_SERVICE_URL } from "../../../config";

const props = defineProps<{ clubId: number }>();
const emit = defineEmits(["created", "cancel"]);

const title = ref("");
const date = ref("");
const time = ref("");
const selectedBook = ref<Book | null>(null);

const { userInfo } = useAuth(); // <-- 2. LẤY USERINFO

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

// 3. SỬA HÀM NÀY
async function createMeeting() {
  // Lấy user_id
  const userId = userInfo.value?.id || userInfo.value?.user_id;

  if (!title.value || !date.value || !time.value) {
    // Sửa lại alert cho đúng (sách là không bắt buộc)
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
    formData.append("user_id", String(userId)); // <-- THÊM USER_ID VÀO FORM

    if (selectedBook.value) {
      formData.append("book_id", String(selectedBook.value.id));
    }

    const res = await axios.post(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}/meetings`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });

    if (res.data && res.data.id) {
        notifyClubMembers(title.value, res.data.id);
    }

    alert("Tạo cuộc họp thành công!");
    emit("created");
  } catch (error: any) {
    console.error("Lỗi khi tạo cuộc họp:", error);
    // Hiển thị lỗi chính xác từ backend
    alert(error.response?.data?.detail || "Tạo cuộc họp thất bại, vui lòng thử lại!");
  }
}

async function notifyClubMembers(meetingTitle: string, meetingId: number) {
  try {
    // 1. Lấy danh sách thành viên
    const res = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}/members`);
    const members = res.data;
    
    // 2. Lấy tên CLB (để hiển thị trong thông báo)
    const clubRes = await axios.get(`${BOOK_SERVICE_URL}bookclubs/${props.clubId}`);
    const clubName = clubRes.data.name;

    const currentUserId = userInfo.value?.id || userInfo.value?.user_id;

    // 3. Gửi thông báo cho từng người (trừ mình)
    for (const member of members) {
        if (member.user_id === currentUserId) continue;
        
        axios.post(`${USER_SERVICE_URL}notifications/add`, {
            receiver_id: member.user_id,
            sender_id: currentUserId,
            type: 'club_meeting',
            message: JSON.stringify({
                title: meetingTitle,
                clubName: clubName,
                meetingId: meetingId
            }),
            status: 'unread'
        }).catch(e => console.error("Lỗi gửi notif:", e));
    }
  } catch (e) { console.error("Lỗi logic notif:", e); }
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