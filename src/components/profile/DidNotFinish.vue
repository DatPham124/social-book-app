<script setup lang="ts">
import axios from "axios";
import { ref, onMounted, watch } from "vue"; // Thêm watch
import { jwtDecode } from "jwt-decode";
import { BOOK_SERVICE_URL } from "../../config.ts"; 
import { useAuth } from "../../composables/useAuth"; 

const props = defineProps<{
    userID?: number | string;
}>();

const books = ref<any[]>([]);
const loading = ref(true);
const errorMessage = ref<string | null>(null);

const { userInfo } = useAuth(); 

async function get_book_by_id(book_id: number) {
  try {
    const response = await axios.get(`${BOOK_SERVICE_URL}books/${book_id}`);
    return response.data;
  } catch (error: any) {
    return null;
  }
}

async function getDidNotFinishBooks() {
  loading.value = true;

  // Logic lấy ID: ưu tiên Props
  const targetID = props.userID ? Number(props.userID) : (userInfo.value?.user_id || userInfo.value?.id);

  if (!targetID) {
    errorMessage.value = "Chưa xác định người dùng";
    loading.value = false;
    return;
  }

  try {
    const response = await axios.get(
      `${BOOK_SERVICE_URL}books/status/book/${targetID}`, // Dùng targetID
      { params: { status: "dnf" } } 
    );
    const statusList = response.data;
    const detailedBooks = await Promise.all(
      statusList.map(async (item: any) => {
        return { ...item, book: await get_book_by_id(item.book_id) };
      })
    );
    books.value = detailedBooks.filter((b) => b.book !== null);
    errorMessage.value = null;
  } catch (error: any) {
    if (axios.isAxiosError(error) && error.response?.status === 404) {
       books.value = []; // 404 nghĩa là không có sách nào
       errorMessage.value = null; 
    } else {
      errorMessage.value = "Lỗi tải sách.";
    }
  } finally {
    loading.value = false;
  }
}

onMounted(getDidNotFinishBooks);

watch(() => props.userID, getDidNotFinishBooks);
</script>

<template>
  <div class="bg-white p-4 rounded-lg shadow border">
    <div class="flex justify-between items-center border-gray-200 pb-2 mb-3">
      <h3 class="text-sm font-semibold text-gray-800 uppercase">Chưa hoàn thành</h3>
      <router-link :to="{ name: 'view_all_dnf_book' }" class="text-sm text-yellow-600 hover:text-yellow-800">
        {{ books.length }} &rarr;
      </router-link>
    </div>
    
    <div class="space-y-2">
      <div v-if="loading" class="text-sm text-gray-500 italic">Đang tải...</div>
      <div v-else-if="errorMessage" class="text-sm text-gray-500 italic">
        {{ errorMessage }}
      </div>
      <div v-if="!loading && books.length == 0" class="text-sm text-gray-500 italic text-center">
        Không có sách nào.
      </div>
    </div>
  </div>
</template>