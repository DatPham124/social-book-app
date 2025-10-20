<script setup lang="ts">
import { onMounted, ref } from 'vue';
import axios from 'axios';
import { Listbox, ListboxButton, ListboxOption, ListboxOptions } from '@headlessui/vue'
import { ChevronUpDownIcon } from '@heroicons/vue/20/solid'
import { BOOK_SERVICE_URL, COVER_IMAGE_SERVER_URL } from '../config.ts'
import { jwtDecode } from 'jwt-decode';

const offset = ref(0);
const limit = 10;
const loadingMore = ref(false);
const hasMore = ref(true);

interface TokenPayLoad {
  username: string
  roles: number[]
  exp: number
  user_id: number
}

const token = localStorage.getItem("token")
let userInfo: TokenPayLoad | null = null

if (token) {
  try {
    userInfo = jwtDecode<TokenPayLoad>(token);
    if (userInfo.exp * 1000 < Date.now()) {
      localStorage.removeItem('token');
      userInfo = null;
    }
  } catch (error) {
    console.error("Invalid token:", error);
    localStorage.removeItem('token');
  }
}

const statuses = [
  { value: 'to_read', label: 'Sẽ đọc' },
  { value: 'currently_reading', label: 'Đang đọc' },
  { value: 'read', label: 'Đã đọc' },
  { value: 'dnf', label: 'Chưa hoàn thành' }
]

const books = ref<any[]>([]);
const errorMessages = ref("");

function mapStatus(statusStr: string) {
  return statuses.find(s => s.value === statusStr) || statuses[0];
}

async function updateBookStatus(bookId: number, newStatus: any) {
  try {
    const userID = userInfo?.user_id;
    await axios.put(`${BOOK_SERVICE_URL}books/${bookId}/status`, null, {
      params: { user_id: userID, status: newStatus.value }
    });

    console.log(`✅ Book ${bookId} updated to status: ${newStatus.value}`);
  } catch (error) {
    console.error("❌ Lỗi khi cập nhật trạng thái:", error);
  }
}

async function getAuthor(authorID: number) {
  try {
    const response = await axios.get(`${BOOK_SERVICE_URL}author/${authorID}`);
    return response.data;
  } catch (error: any) {
    errorMessages.value = axios.isAxiosError(error) && error.response
      ? error.response.data.detail
      : "Không thể kết nối đến server";
    return null;
  }
}

// Hàm mới để lấy categories của sách
async function getBookCategories(bookId: number) {
  try {
    const response = await axios.get(`${BOOK_SERVICE_URL}books/${bookId}/categories`);
    return response.data;
  } catch (error: any) {
    console.error("Lỗi khi lấy categories:", error);
    return [];
  }
}

async function loadMoreBooks() {
  if (!userInfo || loadingMore.value || !hasMore.value) return;
  loadingMore.value = true;
  try {
    const response = await axios.get(
      `${BOOK_SERVICE_URL}books/explore/${userInfo.user_id}`,
      { params: { offset: offset.value, limit } }
    );

    if (response.data.length < limit) {
      hasMore.value = false;
    }

    const newBooks = await Promise.all(
      response.data.map(async (book: any) => {
        const [authorResponse, categoriesResponse] = await Promise.all([
          getAuthor(book.authorID),
          getBookCategories(book.id) // Sửa thành book.id
        ]);

        const authorName = authorResponse ? authorResponse.name : "Không rõ";
        const categoryNames = categoriesResponse && categoriesResponse.length > 0 
          ? categoriesResponse.map((cat: any) => cat.name).join(', ')
          : "Không rõ";

        return {
          ...book,
          authorName,
          categoryName: categoryNames,
          status: { value: "to_read", label: "Sẽ đọc" }
        };
      })
    );

    books.value.push(...newBooks);
    offset.value += limit;
  } catch (error: any) {
    console.error("Lỗi load sách:", error);
  } finally {
    loadingMore.value = false;
  }
}

onMounted(() => {
  loadMoreBooks();
});
</script>

<template>
  <div>
    <div v-if="errorMessages" class="text-red-500 font-semibold text-center mt-4">
      {{ errorMessages }}
    </div>

    <ul v-else-if="books.length > 0">
      <li v-for="book in books" :key="book.id">
        <div class="flex flex-row relative h-60 w-full bg-white rounded-lg shadow-md m-2">
          <div class="relative h-full w-40 flex-shrink-0">
            <img :src="`${COVER_IMAGE_SERVER_URL}/${book.cover_url}`" alt="Book Cover" class="h-full object-contain" />
          </div>

          <div class="m-4 flex-grow">
            <p class="font-bold text-2xl">{{ book.title }}</p>
            <p class="text-gray-600 mt-2">Tác giả: {{ book.authorName }}</p>
            <p class="text-gray-600 mt-2">Thể loại: {{ book.categoryName }}</p>
            <p class="text-gray-600 mt-2">Năm xuất bản: {{ book.published_date }}</p>
            <p class="text-gray-600 mt-2">Mô tả: {{ book.description }}</p>
          </div>

          <div class="p-4 flex items-start justify-end">
            <Listbox v-model="book.status" @update:modelValue="(val) => updateBookStatus(book.id, val)">
              <div class="relative w-48">
                <ListboxButton
                  class="relative w-full cursor-default rounded-md bg-yellow-400 py-2 pl-3 pr-10 text-left text-black shadow-md focus:outline-none focus:ring-2 focus:ring-yellow-500 sm:text-sm">
                  <span class="block truncate">{{ book.status.label }}</span>
                  <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                    <ChevronUpDownIcon class="h-5 w-5 text-black" aria-hidden="true" />
                  </span>
                </ListboxButton>

                <ListboxOptions
                  class="absolute mt-1 max-h-60 w-full overflow-auto rounded-md bg-white py-1 text-base shadow-lg ring-1 ring-black/5 focus:outline-none sm:text-sm">
                  <ListboxOption v-for="status in statuses" :key="status.value" :value="status"
                    v-slot="{ active, selected }">
                    <li :class="[
                      active ? 'bg-yellow-100 text-yellow-900' : 'text-gray-900',
                      'relative cursor-default select-none py-2 pl-10 pr-4'
                    ]">
                      <span :class="[selected ? 'font-medium' : 'font-normal', 'block truncate']">
                        {{ status.label }}
                      </span>
                      <span v-if="selected" class="absolute inset-y-0 left-0 flex items-center pl-3 text-yellow-600">
                        ✔
                      </span>
                    </li>
                  </ListboxOption>
                </ListboxOptions>
              </div>
            </Listbox>
          </div>
        </div>
      </li>
    </ul>

    <div class="text-center mt-4">
      <button v-if="hasMore && !loadingMore" @click="loadMoreBooks"
        class="px-4 py-2 bg-yellow-400 rounded-md hover:bg-yellow-500">
        Tải thêm
      </button>
      <p v-else-if="!hasMore" class="text-gray-500">Đã tải hết sách</p>
      <p v-else class="text-gray-500">Đang tải...</p>
    </div>
  </div>
</template>